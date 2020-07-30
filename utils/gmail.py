import os
import pickle
from typing import List, Optional, Dict, Union, Any
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class GMailAPI:
    """Methods for establishing and building a store of credentials for
    connecting to the GMail API"""
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.labels',  # Write labels
        'https://www.googleapis.com/auth/gmail.settings.basic'  # Read/write filters, read labels
    ]
    DEFAULT_GMAIL_CREDS = os.path.join('creds', 'gmail-credentials.json')
    DEFAULT_PICKLE_PATH = os.path.join('creds', 'token.pickle')

    def __init__(self, google_creds_path: str = DEFAULT_GMAIL_CREDS,
                 pickle_path: str = DEFAULT_PICKLE_PATH):
        self.credentials_path = google_creds_path
        self.pickle_path = pickle_path
        self.service = None
        self.start_service()

    def _look_for_pickles(self) -> Optional[Any]:
        """Checks for a pickle file, indicating that the app has already been authed

        Note: The file token.pickle stores the user's access and refresh tokens, and is
            created automatically when the authorization flow completes for the first
            time.
        """
        if os.path.exists(self.pickle_path):
            with open(self.pickle_path, 'rb') as token:
                return pickle.load(token)
        return None

    def _save_to_pickle(self, creds: Any):
        """Saves credentials to a pickle"""
        with open(self.pickle_path, 'wb') as token:
            pickle.dump(creds, token)

    def get_credentials(self):
        """Handles initial authentication from gmail-credentials
        If a pickle hasn't already been made.
        """
        creds = self._look_for_pickles()
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            self._save_to_pickle(creds)
        return creds

    def start_service(self):
        """Initiates the GMailAPI service"""
        self.service = build('gmail', 'v1', credentials=self.get_credentials())


class GMailLabelAPI(GMailAPI):
    """Label methods
    Docs:
        http://googleapis.github.io/google-api-python-client/docs/dyn/gmail_v1.users.labels.html
        https://developers.google.com/gmail/api/v1/reference/users/labels/create
    """
    def __init__(self):
        super().__init__()
        self.label_actions = self.service.users().labels()

    def get_all_labels(self, label_type: str = 'user') -> List[Dict[str, Union[str, int]]]:
        """Pulls all the gmail labels"""
        results = self.label_actions.list(userId='me').execute()
        labels = results.get('labels', [])
        return [x for x in labels if x['type'] == label_type]

    def get_label(self, label_name: str) -> Optional[Dict[str, Union[str, int]]]:
        """Pulls a specific label
        """
        all_labels = self.get_all_labels()
        for label in all_labels:
            if label['name'] == label_name:
                return label
        return None

    def delete_label(self, label_name: str) -> Optional[Dict[str, Union[str, int]]]:
        """Deletes the specific label
        """
        label = self.get_label(label_name)
        if label is None:
            return None
        resp = self.label_actions.delete(userId='me', id=label['id']).execute()
        return resp

    def create_label(self, label_name: str) -> Dict[str, Union[str, int]]:
        """Creates a new label"""
        new_label = {
            'type': 'user',
            'name': label_name,
            'labelListVisibility': 'labelShowIfUnread',
            'messageListVisibility': 'show'
        }

        resp = self.label_actions.create(userId='me', body=new_label).execute()
        if 'id' in resp.keys():
            print(f'Successfully created label with id {resp["id"]}')
        return resp


class GMailFilterAPI(GMailAPI):
    """Filter methods

    Docs:
        http://googleapis.github.io/google-api-python-client/docs/dyn/gmail_v1.users.settings.filters.html
        https://developers.google.com/gmail/api/v1/reference/users/settings/filters/create

    """
    def __init__(self):
        super().__init__()
        # Roll up the chain of action for filters
        self.filter_actions = self.service.users().settings().filters()

    def list_filters(self) -> List[dict]:
        """Generates a list of filters"""
        resp = self.filter_actions.list(userId='me').execute()
        return resp.get('filter', [])

    def get_filter(self, filter_id: str) -> Optional[dict]:
        """Tries to get a filter by looking for matching ids or query"""
        filters = self.list_filters()
        for filt in filters:
            if filt.get('id') == filter_id:
                return filt
        return None

    def create_filter(self, query: str, actions_dict: Dict[str, List[str]]) -> Dict[str, Union[str, int]]:
        """Builds a new filter"""
        filter_body = {
            'action': actions_dict,
            'criteria': {
                'query': query
            }
        }

        resp = self.filter_actions.create(userId='me', body=filter_body).execute()
        return resp

    def delete_filter(self, filter_id: str = None):
        """Deletes a filter"""
        self.filter_actions.delete(userId='me', id=filter_id).execute()
