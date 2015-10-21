

import _winreg
import platform

def get_key_values(parent_key, key):

    try:
        key_handle = _winreg.OpenKey(parent_key, key)
    except Exception as msg:
        print("Failed to open key '" + key + "'!")
        return []

    values = []
    index = 0
    while index < 999:
        try:
            val = _winreg.EnumValue(key_handle, index)
            values.append(val)
        except Exception as msg:
            break
        index += 1

    return values

def get_installed_vc_versions():

    key = "SOFTWARE\Microsoft\VisualStudio\SxS\VS7\\"
        
    if platform.architecture()[0] == "64bit":
        key = "SOFTWARE\Wow6432Node\Microsoft\VisualStudio\SxS\VS7\\"
    installed_versions = get_key_values(_winreg.HKEY_LOCAL_MACHINE, key)

    merged_values = {}

    for data in installed_versions:
        version, path = data[0], data[1]
        merged_values[version] = path

    return merged_values

if __name__ == "__main__":
    print(get_installed_vc_versions())
