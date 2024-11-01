from unittest.mock import Mock
from gptman.main import (
    get_client,
)
from gptman.assistant import (
    update_instruction,
    list_assistants,
)


class TestGetClient:
    def test_openai_client(self):
        settings = {
            'gptman': {
                'backend': 'openai',
                'api_key': 'fake-api-key',
            }
        }
        assert get_client(settings)

    def test_openai_client_with_profile(self):
        settings = {
            'profile': {
                'profile_a': {
                    'backend': 'openai',
                    'api_key': 'fake-api-key',
                }
            }
        }
        assert get_client(settings, profile='profile_a')

    def test_azure_client(self):
        settings = {
            'gptman': {
                'backend': 'azure',
                'azure_endpoint': 'fake-azure-endpoint',
                'api_version': 'fake-api-version',
                'api_key': 'fake-api-key',
            }
        }
        assert get_client(settings)

    def test_azure_client_with_profile(self):
        settings = {
            'profile': {
                'profile_a': {
                    'backend': 'azure',
                    'azure_endpoint': 'fake-azure-endpoint',
                    'api_version': 'fake-api-version',
                    'api_key': 'fake-api-key',
                }
            }
        }
        assert get_client(settings, profile='profile_a')


class TestUpdateInstruction:
    def test_update(self):
        client = Mock()
        client.beta.assistants.update.return_value = 'return_value'

        assert update_instruction(client, 'test_asst') == 'return_value'
        client.beta.assistants.update.assert_called_with('test_asst')

    def test_update_with_tools(self):
        client = Mock()
        client.beta.assistants.update.return_value = 'return_value'

        assert update_instruction(client, 'test_asst', tools='file_search') == 'return_value'
        client.beta.assistants.update.assert_called_with(
            'test_asst',
            tools=[{'type': 'file_search'}]
        )
