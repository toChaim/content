from CommonServerPython import *
from CommonServerUserPython import *

''' GLOBAL VARS '''

SAMPLE_DATA = {
    'Status': 5,
    'ResponderID': 2043038444649,
    'DueBy': '2019-05-15T08:00:00Z',
    'FrDueBy': '2019-05-14T09:00:00Z',
    'Priority': 3,
    'Source': 1,
    'Tag': [],
    'RequesterID': 2043000056647,
    'UpdatedAt': '2019-05-13T19:52:35Z',
    'AdditionalFields': {
        'IsEscalated': False,
        'Deleted': False,
        'CompanyID': 44002282180,
        'FrEscalated': False,
        'DescriptionHTML': b'<p>Hello there,</p><br /><p>I\xe2\x80\x99m looking to buy a pair of Mary Jane shoes and '
                           b'I noticed that you have a local store in Aldovia. \xcf\x80. Could you let me know if the '
                           b'Mary Jane shoes are available in Size 8? I can pick it up from there.</p><br '
                           b'/><p>Thanks,<br />Emily.</p>'.decode('utf-8'),
        'Spam': False,
        'DescriptionText': b'Hello there,I\xe2\x80\x99m looking to buy a pair of Mary Jane shoes and I noticed that '
                           b'you have a local store in Aldovia. \xcf\x80. Could you let me know if the Mary Jane '
                           b'shoes are available in Size 8? I can pick it up from there.Thanks,Emily.'.decode('utf-8'),
        'Type': 'Question'
    },
    'ID': 1023,
    'CreatedAt': '2019-05-13T19:52:33Z',
    'Subject': 'Mary Jane shoes in Size 8?'
}


''' FUNCTIONS '''


def tbl_to_md_with_non_ascii_chars_nested_dict():
    """
    Call tableToMarkdown with sample data that has nested dict with non-ascii characters inside it
    namely, 'Right Single Quotation Mark' and 'Greek Small Letter Pi'

    Returns
    -------
    unicode
        markdown of SAMPLE_DATA
    """
    title = 'Test'
    human_readable = tableToMarkdown(title, SAMPLE_DATA, removeNull=True)
    return human_readable


def output_of_test_tbl_to_md():
    human_readable = tbl_to_md_with_non_ascii_chars_nested_dict()
    return_outputs(readable_output=human_readable, outputs=SAMPLE_DATA, raw_response=SAMPLE_DATA)


def successful_execute_exit_code():
    tbl_to_md_with_non_ascii_chars_nested_dict()
    return 0


''' EXECUTION '''

# python2 uses __builtin__ python3 uses builtins
if __name__ == "__builtin__" or __name__ == "builtins":
    output_of_test_tbl_to_md()
