import os
import gspread

CREDS_FILE = 'bot/creds.json'


def load_sheet(url):
    clean_data = {}
    if os.path.exists(CREDS_FILE):
        try:
            client = gspread.service_account(filename=CREDS_FILE)
        except Exception as e:
            print("Exception!", e)
            return ({}, e)
    else:
        return ({}, "Google sheets credentials not found")
    sheet = client.open_by_url(url)
    worksheet = sheet.get_worksheet(0)
    try:
        data = worksheet.get_all_records()

        decks = {}
        for row in data:
            if row['deck'] == 'option':
                if row['header'] == 'gameTitle':
                    clean_data['title'] = row['body']
            else:
                try:
                    deck_number = int(row['deck'])
                    if deck_number == 0:
                        # skip instructions
                        continue
                    if deck_number not in decks:
                        decks[deck_number] = []
                    text = row['body']
                    if row['header']:
                        text = f"{row['header']} - {text}"
                    decks[deck_number].append(text)
                except ValueError:
                    continue
        final = max(decks.keys())
        clean_data['final'] = decks[final]
        clean_data['prompts'] = [prompt for deck, prompt_list in decks.items()
                                 for prompt in prompt_list if deck != final]
    except gspread.GSpreadException as e:
        print("Exception!", e)
        return ({}, e)
    return (clean_data, None)
