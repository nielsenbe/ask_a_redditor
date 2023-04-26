import zstandard
import os
import json
import logging.handlers
import csv

log = logging.getLogger("bot")
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())


def read_and_decode(reader, chunk_size, max_window_size, previous_chunk=None, bytes_read=0):
	chunk = reader.read(chunk_size)
	bytes_read += chunk_size
	if previous_chunk is not None:
		chunk = previous_chunk + chunk
	try:
		return chunk.decode()
	except UnicodeDecodeError:
		if bytes_read > max_window_size:
			raise UnicodeError(f"Unable to decode frame after reading {bytes_read:,} bytes")
		log.info(f"Decoding error with {bytes_read:,} bytes, reading another chunk")
		return read_and_decode(reader, chunk_size, max_window_size, chunk, bytes_read)


def read_lines_zst(file_name):
	with open(file_name, 'rb') as file_handle:
		buffer = ''
		reader = zstandard.ZstdDecompressor(max_window_size=2**31).stream_reader(file_handle)
		while True:
			chunk = read_and_decode(reader, 2**27, (2**29) * 2)

			if not chunk:
				break
			lines = (buffer + chunk).split("\n")

			for line in lines[:-1]:
				yield line, file_handle.tell()

			buffer = lines[-1]

		reader.close()


def create_candidate_submissions_file(directory, date):
    """
    For a given Pushshift Submission file:
    1. Stream decompress zstandard format
    2. Do some high level filtering of submissions:
        a. is_self == True
        b. sticked == False
        c. title ends with ? or starts with IWTL
        d. subreddit in list
    3. Save list of submission ids to another folder for further processing.
    """
    file_path = os.path.join(directory, '0_RawData', f'RS_{date}.zst')
    output_path = os.path.join(directory, '1_CandidateSubmissions', f'RS_{date}.csv')
    file_size = os.stat(file_path).st_size
    file_lines = 0
    file_bytes_processed = 0
    bad_lines = 0
    
    with open(output_path, 'w', newline='\n', encoding="utf-8") as f:
        writer = csv.writer(f, delimiter='|')
        for line, file_bytes_processed in read_lines_zst(file_path):
            try:
                obj = json.loads(line)
                if obj['is_self'] == True and obj['stickied'] == False and (obj['title'].endswith('?') or obj['title'].startswith('IWTL')) and obj['subreddit'] in [
                    'askscience',
                    'AskHistorians',
                    'answers',
                    'askphilosophy',
                    'AskEngineers',
                    'TrueAskReddit',
                    'AskCulinary',
                    'NoStupidQuestions',
                    'explainlikeimfive',
                    'AskSocialScience',
                    'AskDocs',
                    'Advice',
                    'legaladvice',
                    'AskAnthropology',
                    'IWantToLearn']:
                    writer.writerow([obj['name']])
         
            except (KeyError, json.JSONDecodeError) as err:
                bad_lines += 1
            file_lines += 1
            if file_lines % 100000 == 0:
                log.info(f" {file_lines:,} : {bad_lines:,} : {file_bytes_processed:,}:{(file_bytes_processed / file_size) * 100:.0f}%")

    log.info(f"Complete : {file_lines:,} : {bad_lines:,}")
