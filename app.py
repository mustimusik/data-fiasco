import streamlit as st
import pygsheets
import pandas as pd
import regex  as re
import json
import ast
from google.oauth2 import service_account

st.title("Input Data to Database")

def open_google_sheet(sheet_title, worksheet_title):
  secret_dict = st.secrets["CREDENTIALS"]

  SCOPES = ('https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive')
  service_account_info = json.loads(json.dumps(dict(secret_dict)))
  my_credentials = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
  gc = pygsheets.authorize(custom_credentials=my_credentials)
  sheet = gc.open(sheet_title)
  worksheet = sheet.worksheet_by_title(worksheet_title)
  return worksheet

def read_worksheet(worksheet, header=True):
  return worksheet.get_as_df(has_header=header)

def write_to_worksheet(worksheet, data, start='A1', index=False, header=True):
  worksheet.set_dataframe(pd.DataFrame(data), start=start, copy_index=index, copy_head=header)
  
def insert_to_event(event_list_worksheet, event_list, jenis_event, tanggal_event):
  nama_event = jenis_event.replace(" ", "_") + "_" + tanggal_event.replace(" ", "_")

  id_new_data_event = len(event_list) + 1
  new_data_event = pd.DataFrame({"id_event":[id_new_data_event], "nama_event":[nama_event], "tanggal_event":[tanggal_event]})
  new_event_list = pd.concat([event_list, new_data_event], axis=0, ignore_index=True)

  write_to_worksheet(event_list_worksheet, new_event_list, start='A1', index=False, header=True)

  return new_event_list

def insert_to_user(user_worksheet, user, new_user):
  start = 0
  end = len(user) + len(new_user)
  if len(user) != 0:
    start = user['id_user'].values.max()+1
    end = start + len(new_user)
  id_new_user = range(start, end)

  new_user = new_user.copy()
  user = user.copy()

  new_user['id_user'] = id_new_user
  new_user = new_user[['id_user', 'nama_user', 'email_user', 'nomor_user']]

  updated_user = pd.concat([user, new_user], axis=0, ignore_index=True)
  updated_user.drop_duplicates(subset=['email_user'], inplace=True)
  updated_user['id_user'] = range(1, len(updated_user)+1)
  updated_user['nomor_user'] = updated_user['nomor_user'].map(preprocess_nomor)
  write_to_worksheet(user_worksheet, updated_user)

  return updated_user

def insert_to_event_log(event_log_worksheet, event_list, event_log, user, new_user, tanggal_event):
  participant_log = new_user.copy()

  merged = participant_log.merge(user, on='email_user', how='left')

  id_event = event_list[event_list['tanggal_event'] == tanggal_event]['id_event'].values[0]

  sources = merged['source'].values.tolist()
  start = 0
  end = len(event_log) + len(merged)
  if len(event_log) != 0:
    start = event_log['id_log'].values.max()+1
    end = start + len(merged)
  new_id_log = range(start, end)
  sources = ['WA' if x == 'WhatsApp' else x.upper() for x in sources]
  new_id_user = merged['id_user'].values.tolist()
  
  new_event_log = pd.DataFrame({
    'id_log':new_id_log,
    'id_user':new_id_user,
    'source':sources
  })

  new_event_log['id_event'] = id_event
  new_event_log = new_event_log[event_log.columns]

  new_event_log_merged = pd.concat([event_log, new_event_log], axis=0, ignore_index=True)

  write_to_worksheet(event_log_worksheet, new_event_log_merged)

  return new_event_log

def insert_to_event_transaction(event_transaction_worksheet, event_transaction, buyer, user, event_log):
  merged = buyer.merge(user, on='email_user', how='left')
  merged['id_user'].fillna(-1, inplace=True)
  merged['id_user'] = merged['id_user'].astype('int64')

  merged_2 = merged.merge(event_log, on='id_user', how='left')
  # last_event_index = event_log[['id_event']].iloc[-1].values[0]
  # merged_2 = merged_2[merged_2['id_event']==last_event_index]
  print(len(merged_2))
  merged_2.drop_duplicates(subset=['id_user'], keep='last', inplace=True)
  merged_2['id_log'].fillna(-1, inplace=True)
  merged_2['id_log'] = merged_2['id_log'].astype('int64')
  start = 0
  end = len(event_transaction) + len(buyer)
  if len(event_transaction) != 0:
    start = event_transaction['id_transaction'].values.max()+1
    end = start + len(buyer)
  new_id_transaction = range(start, end)
  new_id_log = merged_2[['id_log']].values.reshape(-1)
  new_paket = merged_2[['paket']].values.reshape(-1)
  new_paket = [x.upper() for x in new_paket]
  new_nominal = merged_2[['nominal']].values.reshape(-1)
  new_diskon = merged_2[['diskon']].values.reshape(-1)
  print(len(merged_2))
  print(start, end, len(new_id_transaction), len(new_id_log), len(new_paket), len(new_nominal), len(new_diskon))
  new_transaction = pd.DataFrame({
    'id_transaction':new_id_transaction,
    'id_log':new_id_log,
    'paket':new_paket,
    'nominal':new_nominal,
    'diskon':new_diskon
  })

  new_transaction_merged = pd.concat([event_transaction, new_transaction], axis=0, ignore_index=True)

  write_to_worksheet(event_transaction_worksheet, new_transaction_merged)

  return new_transaction_merged

def insert_to_registered_user(registered_user_worksheet, registered_user, data_member_terbaru, buyer, user):
  data_member_terbaru_filtered = data_member_terbaru[['user_email', 'user_registered_merge', 'user_expired_merge']].copy()
  new_registered_user = buyer.merge(user, on='email_user', how='left')
  new_registered_user = new_registered_user.merge(data_member_terbaru_filtered, left_on='email_user', right_on='user_email', how='left').copy()[['id_user', 'email_user', 'nomor_user_x', 'user_registered_merge', 'user_expired_merge']]
  new_registered_user.columns=['id', 'email', 'nomor', 'created_at', 'expired_at']
  new_registered_user_merged = pd.concat([registered_user, new_registered_user], axis=0, ignore_index=True)
  new_registered_user_merged['nomor'] = new_registered_user_merged['nomor'].map(preprocess_nomor)
  write_to_worksheet(registered_user_worksheet, new_registered_user_merged)

  return new_registered_user_merged

def extract_data_free_class(new_data):
  new_user = pd.DataFrame({"nama_user":[], "email_user":[], "nomor_user":[]})
  i = 11
  for j in range(i, new_data.columns[-1], 3):
    temp_user = pd.DataFrame()
    nama = new_data[[j]].loc[2:].values.reshape(-1)
    nama = nama[nama!='']
    email = new_data[[j+1]].loc[2:].values.reshape(-1)
    email = email[email!='']
    nomor = new_data[[j+2]].loc[2:].values.reshape(-1)
    nomor = nomor[nomor!='']
    temp_user = pd.DataFrame({"nama_user":nama, "email_user":email, "nomor_user":nomor})
    temp_user['source'] = new_data[[j]].loc[0].values[0]
    new_user = pd.concat([new_user, temp_user], axis=0, ignore_index=True)
  new_user.drop_duplicates(subset=['email_user'], inplace=True)
  buyer = new_data[new_data[1]!=""][range(1, 8)].loc[2:].copy()
  buyer.columns = ['asal','nama_user','email_user','nomor_user','paket','diskon','nominal']
  
  return new_user, buyer

def extract_data_bootcamp(new_data):
  new_user = pd.DataFrame({"nama_user":[], "email_user":[], "nomor_user":[]})
  for j in range(0, new_data.columns[-1], 3):
    temp_user = pd.DataFrame()
    nama = new_data[[j]].loc[2:].values.reshape(-1)
    nama = nama[nama!='']
    email = new_data[[j+1]].loc[2:].values.reshape(-1)
    email = email[email!='']
    nomor = new_data[[j+2]].loc[2:].values.reshape(-1)
    nomor = nomor[nomor!='']
    temp_user = pd.DataFrame({"nama_user":nama, "email_user":email, "nomor_user":nomor})
    temp_user['source'] = new_data[[j]].loc[0].values[0]
    new_user = pd.concat([new_user, temp_user], axis=0, ignore_index=True)
  new_user.drop_duplicates(subset=['email_user'], inplace=True)
  return new_user

def preprocess_nomor(nomor):
  nomor = str(nomor)
  result = re.sub('\D', '', nomor)
  if len(result) == 0:
    return result
  if result[0] == '8':
    result = '62' + result
  return result

def insert_to_visualization(visualization_worksheet, user, event_log, event_list, event_transaction):
  events = event_log.merge(event_list, on="id_event")
  # events = events[events.columns[:-1]]
  user_log = user.merge(events, on="id_user", validate="one_to_many")
  st.write(len(user_log))
  st.write(len(user_log.columns))
  user_transaction = user_log.merge(event_transaction, on="id_log", how="left")
  st.write(len(user_transaction))
  st.write(len(user_transaction.columns))
  user_transaction["nominal"] = user_transaction["nominal"].map(get_only_num)
  user_transaction["buyer"] = "buyer"
  user_transaction.loc[user_transaction["diskon"].isna(), "buyer"] = "tidak"

  write_to_worksheet(visualization_worksheet, user_transaction)

  return user_transaction

def get_only_num(number):
  number = str(number)
  if number == "nan":
    return 0
  cleaned_number = re.sub('\D', '', number)
  # converted_number = int(cleaned_number)
  return cleaned_number

def preprocess_buyer(row):
  if str(row["diskon"]) == "nan":
    row["buyer"] = "tidak"
  return row

def insert_to_unregisted_user(unregistered_user_worksheet, user, event_log, event_transaction):
  unregist = user.merge(event_log, on='id_user', how='left').merge(event_transaction, on="id_log", how="left")
  unregist = unregist[unregist['id_transaction'].isna()].drop_duplicates(subset="id_user")
  unregist = unregist[user.columns]
  write_to_worksheet(unregistered_user_worksheet, unregist)

  return unregist

def main():
  password = st.text_input("Enter a password", type="password")
  if password == st.secrets["PASSWORD"]:
    sheet_title = "Data Free Class & Bootcamp"
    free_class = "FREE CLASS 2024"
    bootcamp = "BOOTCAMP 2024"
    visualization_title = "Data Free Class & Bootcamp for Visualization"
    worksheet_titles = ['event_list', 'user', 'event_log', 'event_transaction', 'registered_user', 'unregistered_user', 'data_member_terbaru']
    
    event_list_worksheet = open_google_sheet(sheet_title, worksheet_titles[0])
    event_list = read_worksheet(event_list_worksheet)
    
    jenis_event = st.radio(
      "Choose event type",
      ["Free Class", "Bootcamp"],
    )
    tanggal_event = st.text_input("Enter some event date or month")
    
    if not tanggal_event or not jenis_event:
      st.warning("Please enter both event date and type to proceed.")
      return
    if tanggal_event in event_list['tanggal_event'].values:
      st.write('sudah ada')
      return
    else:
      try:
        if jenis_event == "Free Class":
          new_worksheet = open_google_sheet(free_class, tanggal_event)
          new_data = read_worksheet(new_worksheet, header=False)
        else:
          new_worksheet = open_google_sheet(bootcamp, tanggal_event)
          new_data = read_worksheet(new_worksheet, header=False)
      except pygsheets.exceptions.WorksheetNotFound as e:
        st.error(f"Worksheet not found: {e}")
        return
    
      bar = st.progress(0, text="reading data")
      user_worksheet = open_google_sheet(sheet_title, worksheet_titles[1])
      event_log_worksheet = open_google_sheet(sheet_title, worksheet_titles[2])
      event_transaction_worksheet = open_google_sheet(sheet_title, worksheet_titles[3])
      registered_user_worksheet = open_google_sheet(sheet_title, worksheet_titles[4])
      unregistered_user_worksheet = open_google_sheet(sheet_title, worksheet_titles[5])
      data_member_terbaru_worksheet = open_google_sheet(sheet_title, worksheet_titles[6])
      visualization_worksheet = open_google_sheet(visualization_title, "Sheet1")
      
      user = read_worksheet(user_worksheet)
      event_log = read_worksheet(event_log_worksheet)
      event_transaction = read_worksheet(event_transaction_worksheet)
      registered_user = read_worksheet(registered_user_worksheet)
      unregistered_user = read_worksheet(unregistered_user_worksheet)
      data_member_terbaru = read_worksheet(data_member_terbaru_worksheet)
      visualization = read_worksheet(visualization_worksheet)
      
      bar.progress(20, text="input to event list")
      insert_to_event(event_list_worksheet, event_list, jenis_event, tanggal_event)
      event_list = read_worksheet(event_list_worksheet)
      
      if jenis_event == "Free Class":
        new_user, buyer = extract_data_free_class(new_data)
      else:
        new_user = extract_data_bootcamp(new_data)
      
      bar.progress(50, text="input to user")
      insert_to_user(user_worksheet, user, new_user)
      user = read_worksheet(user_worksheet)
      
      bar.progress(70, text="input to event_log")
      insert_to_event_log(event_log_worksheet, event_list, event_log, user, new_user, tanggal_event)
      event_log = read_worksheet(event_log_worksheet)
      
      bar.progress(80, text="input to event_transactin")
      if jenis_event == "Free Class":
        insert_to_event_transaction(event_transaction_worksheet, event_transaction, buyer, user, event_log)
        event_transaction = read_worksheet(event_transaction_worksheet)
      
        bar.progress(90, text="input to registered_user")
        insert_to_registered_user(registered_user_worksheet, registered_user, data_member_terbaru, buyer, user)

      insert_to_unregisted_user(unregistered_user_worksheet, user, event_log, event_transaction)
      bar.progress(95, text="insert to visualization")
      insert_to_visualization(visualization_worksheet, user, event_log, event_list, event_transaction)
      bar.progress(100, text="completed")
      bar.empty()
      st.write("Done")
if __name__ == "__main__":
  main()
