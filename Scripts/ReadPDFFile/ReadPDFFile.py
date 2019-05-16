import demistomock as demisto
from CommonServerPython import *

import subprocess
import glob
import os
import re
import errno
import shutil
from typing import List

ROOT_PATH = os.getcwd()
USER_PASSWORD = demisto.args().get('userPassword')
MAX_IMAGES = int(demisto.args().get('maxImages', 20))


def mark_suspicious(suspicious_reason, entry_id):
    """Missing EOF, file may be corrupted or suspicious file"""

    dbot = {
        "DBotScore":
            {
                "Indicator": entry_id,
                "Type": "file",
                "Vendor": "PDFx",
                "Score": 2
            }
    }
    human_readable = "{}, file marked as suspicious for entry id: {}".format(suspicious_reason, entry_id)
    return_outputs(human_readable, dbot, {})


def run_shell_command(command, *args):
    cmd = [command] + list(args)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    o, e = proc.communicate()
    return o.decode('utf8'), e.decode('utf8')


def get_files_names_in_path(path, name_of_file, full_path=False):
    os.chdir(ROOT_PATH)
    os.chdir(path)
    res = []
    for file_path in glob.glob(name_of_file):
        if full_path:
            file_path = f'{path}/{file_path}'
        res.append(file_path)
    return res


def get_images_paths_in_path(path):
    """
    Gets images paths from path
    :param path: path to look files in
    :return: image path array
    :rtype: ``list``
    """
    res: List[str] = []
    res.extend(get_files_names_in_path(path, "*.ppm", True))
    res.extend(get_files_names_in_path(path, "*.bpm", True))
    res.extend(get_files_names_in_path(path, "*.jpg", True))
    res.extend(get_files_names_in_path(path, "*.png", True))
    return res


def get_pdf_metadata(file_path):
    """Gets the metadata from the pdf as a dictionary"""
    if USER_PASSWORD:
        metadata_txt, e = run_shell_command('pdfinfo', '-upw', USER_PASSWORD, file_path)
    else:
        metadata_txt, e = run_shell_command('pdfinfo', file_path)
    if e:
        raise TypeError(e)
    metadata = {}
    for line in metadata_txt.split('\n'):
        # split to [key, value...]
        line_arr = line.split(':')
        if len(line_arr) > 1:
            key = line_arr[0]
            # handle values with and without ':'
            value = ''
            for i in range(1, len(line_arr)):
                value += line_arr[i].strip() + ':'
            # remove redundant ':'
            value = value[:-1]
            metadata[key] = value
    return metadata


def get_pdf_text(file_path, pdf_text_output_path):
    """Creates a txt file from the pdf in the pdf_text_output_path and returns the content of the txt file"""
    if USER_PASSWORD:
        o, e = run_shell_command('pdftotext', '-upw', USER_PASSWORD, file_path, pdf_text_output_path)
    else:
        o, e = run_shell_command('pdftotext', file_path, pdf_text_output_path)
    if e:
        raise TypeError(e)
    text = ''
    with open(pdf_text_output_path, 'rb') as f:
        for line in f:
            text += line.decode('utf-8')
    return text


def get_pdf_htmls_content(pdf_path, output_folder):
    """Creates an html file and images from the pdf in output_folder and returns the text content of the html files"""
    pdf_html_output_path = f'{output_folder}/PDF.html'
    if USER_PASSWORD:
        o, e = run_shell_command('pdftohtml', '-upw', USER_PASSWORD, pdf_path, pdf_html_output_path)
    else:
        o, e = run_shell_command('pdftohtml', pdf_path, pdf_html_output_path)
    if e:
        raise TypeError(e)
    html_file_names = get_files_names_in_path(output_folder, '*.html')
    html_content = ''
    for file_name in html_file_names:
        with open(file_name, 'rb') as f:
            for line in f:
                html_content += line.decode('utf-8')
    return html_content


def build_readpdf_entry_object(pdf_file, metadata, text, urls, images):
    # Add Text to file entity
    pdf_file["Text"] = text

    # Add Metadata to file entity
    for k in metadata.keys():
        pdf_file[k] = metadata[k]

    md = "### Metadata\n"
    md += "* " if metadata else ""
    md += "\n* ".join(["{0}: {1}".format(k, v) for k, v in metadata.items()])

    md += "\n### URLs\n"
    md += "* " if urls else ""
    md += "\n* ".join(["{0}".format(str(k["Data"])) for k in urls])

    md += "\n### Text"
    md += "\n{0}".format(text)
    results = [{"Type": entryTypes["note"],
                "ContentsFormat": formats["markdown"],
                "Contents": md,
                "HumanReadable": md,
                "EntryContext": {"File(val.EntryID == obj.EntryID)": pdf_file, "URL": urls}
                }]
    if images:
        results[0]['HumanReadable'] = f"{results[0]['HumanReadable']}\n### Images"
        os.chdir(ROOT_PATH)
        for i, img in enumerate(images):
            if i >= MAX_IMAGES:
                break
            file = file_result_existing_file(img)
            results.append(file)
    all_pdf_data = ""
    if metadata:
        for k, v in metadata.items():
            all_pdf_data += str(v)
    if text:
        all_pdf_data += text
    if urls:
        for u in urls:
            u = u["Data"] + " "
            all_pdf_data += u

    # Extract indicators (omitting context output, letting auto-extract work)
    indicators_hr = demisto.executeCommand("extractIndicators", {
        "text": all_pdf_data})[0][u"Contents"]
    results.append({
        "Type": entryTypes["note"],
        "ContentsFormat": formats["json"],
        "Contents": indicators_hr,
        "HumanReadable": indicators_hr
    })
    return results


def main():
    entry_id = demisto.args()["entryID"]
    # File entity
    pdf_file = {
        "EntryID": entry_id
    }

    # URLS
    urls_ec = []
    folders_to_remove = []
    try:
        path = demisto.getFilePath(entry_id).get('path')
        if path:
            try:
                output_folder = "ReadPDF"
                os.makedirs(output_folder)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise e
                pass
            try:
                folders_to_remove.append(output_folder)
                cpy_file_path = f'{output_folder}/ReadPDF.pdf'
                shutil.copy(path, cpy_file_path)
                # Get metadata:
                metadata = get_pdf_metadata(cpy_file_path)
                # Get text:
                pdf_text_output_path = f'{output_folder}/PDFText.txt'
                text = get_pdf_text(cpy_file_path, pdf_text_output_path)
                # Get URLS + Images:
                pdf_html_content = get_pdf_htmls_content(cpy_file_path, output_folder)
                urls = re.findall(urlRegex, pdf_html_content)
                urls_set = set(urls)
                # this url is always generated with the pdf html file, and that's why we remove it
                urls_set.remove('http://www.w3.org/1999/xhtml')
                for url in urls_set:
                    urls_ec.append({"Data": url})
                images = get_images_paths_in_path(output_folder)

            except Exception as e:
                demisto.results({
                    "Type": entryTypes["error"],
                    "ContentsFormat": formats["text"],
                    "Contents": "Could not load pdf file in EntryID {0}\nError: {1}".format(entry_id, str(e))
                })
                raise e
            readpdf_entry_object = build_readpdf_entry_object(pdf_file, metadata, text, urls_ec, images)
            demisto.results(readpdf_entry_object)
        else:
            demisto.results({
                "Type": entryTypes["error"],
                "ContentsFormat": formats["text"],
                "Contents": "EntryID {0} path could not be found".format(entry_id)
            })
    except Exception as e:
        mark_suspicious(f'The script failed read PDF file due to an error: {str(e)}', entry_id)
    finally:
        os.chdir(ROOT_PATH)
        for folder in folders_to_remove:
            shutil.rmtree(folder)


# python2 uses __builtin__ python3 uses builtins
if __name__ == "__builtin__" or __name__ == "builtins":
    main()