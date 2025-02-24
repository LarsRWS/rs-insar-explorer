import re
from datetime import datetime
import numpy as np
from qgis.core import QgsMapLayer, QgsFeature


def checkVectorLayer(layer):
    """ check layer is a valid vector layer """

    if layer is None:
        message = '<span style="color:red;">Invalid Layer: Please select a valid vector layer.</span>'
        return False, message
    elif not layer.isValid():
        message = '<span style="color:red;">Invalid Layer: Please select a valid vector layer.</span>'
        return False, message
    elif not (layer.type() == QgsMapLayer.VectorLayer):
        message = '<span style="color:red;">This is not a vector layer: Please select a valid vector layer.</span>'
        return False, message
    elif layer.geometryType() not in [0, 2]:
        message = '<span style="color:red;">Invalid Layer: Please select a valid point or polygon layer.</span>'
        return False, message
    else:
        return True, ""


def getVectorVelocityFieldName(layer):
    """ check layer is a valid vector with velocity """

    rgx_dt = r'(.*)(vel|deformation.?rate|mean.?deformation)(.*)'
    pattern = re.compile(rgx_dt, re.IGNORECASE)
    field_name = None
    message = ""

    keys_uncertainty = ['err', 'sigma', 'std']
    matches = []
    for field in layer.fields():
        p = pattern.match(field.name())
        if not p:
            continue

        # Check if this is not an uncertainty layer of the velocity
        if any([ele in field.name() for ele in keys_uncertainty]):
            continue

        matches.append(field.name())

    # 0 to n matches possible
    if not matches:
        field_name = None
    elif len(matches) > 1:
        velocity_field_name_options = ['velocity', 'VEL', 'mean_velocity', 'deformation rate']
        # Pick the one with an exact substring match, otherwise just take the first
        field_name = matches[0]
        for velocity_field_name in velocity_field_name_options:
            for match in matches:
                if velocity_field_name in match:
                    field_name = match
                    break
            else:
                break
    else:
        field_name = matches[0]

    if field_name is None:
        message = ('<span style="color:red;">Invalid Layer: Please select a vector layer with valid velocity field.</span>')

    return field_name, message


def checkVectorLayerTimeseries(layer):
    """ check layer is a valid vector with velocity """
    rgx_dt = r'(.*)((19|20)\d{2}[\s\-\._]?[01]\d[\s\-\.]?[0123]\d)T?([012]\d[:\.]?[0-5]\d[0-5]?\d?)?(.*)'
    pattern = re.compile(rgx_dt, re.IGNORECASE)

    count = 0
    message = ""

    status, message = checkVectorLayer(layer)
    if status is False:
        return status, message

    status = False
    for field in layer.fields():
        p = pattern.match(field.name())
        if p:
            status = True
            break
    else:
        message = (f'<span style="color:red;">Invalid Layer: Please select a vector or raster layer with valid timeseries data.')

    return status, message


def getFeatureAttributes(feature: QgsFeature) -> dict:
    """
    Get the attributes of a feature as a dictionary.
    :param feature: QgsFeature
    :return: Dictionary of feature attributes
    """
    return {field.name(): feature[field.name()] for field in feature.fields()}


def extractDateValueAttributes(attributes: dict) -> list:
    """
    Extract attributes with keys in the format 'DYYYYMMDD' or 'YYYYMMDD' and return a list of tuples with datetime and
    float value.
    :param attributes: Dictionary of feature attributes
    :return: List of tuples (datetime, float)
    """
    rgx_dt = r'(.*)((19|20)\d{2}[\s\-\._]?[01]\d[\s\-\.]?[0123]\d)T?([012]\d[:\.]?[0-5]\d[0-5]?\d?)?(.*)'
    pattern = re.compile(rgx_dt)
    d_dt_fmt = {8: '%Y%m%d', 12: '%Y%m%d%H%M', 14: '%Y%m%d%H%M%S'}

    d_date_value = {'los': [], 'h': [], 'v': [], 'los_sigma': [], 'h_sigma': [], 'v_sigma': []}
    keys_uncertainty = ['err', 'sigma', 'std']
    for key, value in attributes.items():
	
        p = pattern.match(key.lower())
        # Skip if no match
        if not p:
            continue

        # Some values are NULL
        try:
            value = float(value)
        except Exception as _:
            value = np.nan
			
        # Groups: 1) string before, 2) date, 3) -, 4) time, 5) string after
        s_before = '' if p.group(1) is None else p.group(1) 
        s_date = '' if p.group(2) is None else p.group(2) 
        s_time = '' if p.group(4) is None else p.group(4) 
        s_after = '' if p.group(5) is None else p.group(5) 

        datetime_str = re.sub(r'[\s:\.\-_]?', '', s_date+s_time)
        date_obj = datetime.strptime(datetime_str, d_dt_fmt[len(datetime_str)])
        s_tag = re.sub(r'[\s:\.\-_]?', '', s_before+s_after)
        key_add = '_sigma' if any([ele in s_tag for ele in keys_uncertainty]) else ''

        # Assign
        if not s_tag or 'los' in s_tag:
            d_date_value['los'+key_add].append((date_obj, float(value)))
        elif 'h' in s_tag:
            d_date_value['h'+key_add].append((date_obj, float(value)))
        elif 'v' in s_tag:
            d_date_value['v'+key_add].append((date_obj, float(value)))
        else:
            d_date_value['los'+key_add].append((date_obj, float(value)))
            
    # Convert to numpy
    for key in d_date_value.keys():
        d_date_value[key] = np.array(d_date_value[key], dtype=object)

    #return np.array(date_value_list, dtype=object)
    return d_date_value


def getVectorFields(layer):
    """ get field names from vector layer"""
    fields = [field.name() for field in layer.fields()]
    return fields
