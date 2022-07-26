import requests

import config as cfg


def get_token(scope):
    url = 'https://cloud.uipath.com/identity_/connect/token'
    data = {
        'grant_type': 'client_credentials',
        'client_id': cfg.app_id,
        'client_secret': cfg.app_secret,
        'scope': scope
    }
    r = requests.post(url, data=data)
    token = 'Bearer ' + r.json()['access_token']
    return token


# Get folders
def get_folders():
    url = f"{cfg.url}/{cfg.org}/{cfg.tenant}/orchestrator_/odata/folders"
    data = {
        'content-type': 'application/json',
        'X-UIPATH-TenantName': cfg.tenant,
        'Authorization': get_token('OR.Folders')
    }
    r = requests.get(url, headers=data)
    return r.json()['value']


def get_folder(folder_name):
    folders = get_folders()
    return str([_['Id'] for _ in folders
                if _['DisplayName'].upper() == folder_name.upper()][0])


# Get releases
def get_releases(folder_id: str):
    url = f"{cfg.url}/{cfg.org}/{cfg.tenant}/orchestrator_/odata/releases"
    data = {
        'content-type': 'application/json',
        'X-UIPATH-TenantName': cfg.tenant,
        'X-UIPATH-OrganizationUnitId': folder_id,
        'Authorization': get_token('OR.Execution')
    }
    r = requests.get(url, headers=data)
    return r.json()['value']


# Get key
def get_key(folder_name, process_name):
    folder_id = get_folder(folder_name)
    releases = get_releases(folder_id)
    return [_['Key'] for _ in releases
            if _['Name'].upper() == process_name.upper()][0]


# Run job
def run_job(folder_name, process_name, args=None):
    url = f"{cfg.url}/{cfg.org}/{cfg.tenant}/" \
          f"orchestrator_/odata/Jobs/UiPath.Server.Configuration.OData.StartJobs"
    data = """
            {
                "startInfo": {
                    "ReleaseKey": "<<ReleaseKey>>",
                    "Strategy": "RobotCount",
                    "RobotIds": [],
                    "NoOfRobots": "1",
                    "InputArguments": "{<<Args>>}"
                }
            }
            """
    data = data.replace('<<ReleaseKey>>', get_key(folder_name, process_name))

    if args:
        data = data.replace('<<Args>>', args)
    else:
        data = data.replace('<<Args>>', '')

    data = data.replace("\n", "").strip()

    headers = {
        'content-type': 'application/json',
        'X-UIPATH-TenantName': cfg.tenant,
        'Authorization': get_token('OR.Jobs'),
        'X-UIPATH-OrganizationUnitId': get_folder(folder_name)
    }

    r = requests.post(url, data=data, headers=headers)
    if r.status_code == 201:
        print(f'Job {process_name} started successfully')


def build_args(args: dict):
    args_str = ''
    for key, value in args.items():
        args_str += '\\"' + key + '\\":\\"' + value + '\\",'
    return args_str[:-1]


if __name__ == '__main__':
    args_ = {
        'in_To': 'testArgs@Gmail.com',
        'in_Subject': 'Test',
        'in_Body': 'Test Notification',
        'in_Name': 'Test Server',
    }

    run_job('Default', 'Email Sender', args=build_args(args_))
