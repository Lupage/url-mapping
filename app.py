from classes import Page
from bs4 import BeautifulSoup, SoupStrainer
from polyfuzz import PolyFuzz
import base64
import concurrent.futures
import pandas as pd
import requests
import streamlit as st

#Function for getting content
def get_content(url_argument):
	page_source = requests.get(url_argument).text
	strainer = SoupStrainer('p')
	soup = BeautifulSoup(page_source, 'lxml', parse_only=strainer)
	paragraph_list = [element.text for element in soup.find_all(strainer)]
	content = " ".join(paragraph_list)
	return content

#Main function start
def get_similarities(url_list_1, url_list_2):
#Concurrency/threading
	with concurrent.futures.ThreadPoolExecutor() as executor:
		content_list_1 = list(executor.map(get_content, url_list_1))
		content_list_2 = list(executor.map(get_content, url_list_2))
  
#Create a dictionary for 2nd content list "url":"content". This is for later map function
	content_dictionary = dict(zip(url_list_2, content_list_2))

#Polyfuzz library start
	model = PolyFuzz("TF-IDF")
	model.match(content_list_1, content_list_2)
	data = model.get_matches()

#Map the Polyfuzz content result to URLs
	def get_key(val):
		for key, value in content_dictionary.items():
			if val == value:
				return key
		return key
	
	with concurrent.futures.ThreadPoolExecutor() as executor:
		result = list(executor.map(get_key, data["To"]))

#Dataframe creation
	to_zip = zip(url_list_1, result, data["Similarity"])
	df = pd.DataFrame(to_zip)
	df.columns = ["From URL", "To URL", "% Identical"]
# 	page_title_from = [Page(element).page_title() for element in df["From URL"]]
# 	df["Page Title of 'From URL'"] = page_title_from
# 	page_title_to = [Page(element).page_title() for element in df["To URL"]]
# 	df["Page Title of 'To URL'"] = page_title_to
# 	df = df[["From URL", "Page Title of 'From URL'", "To URL", "Page Title of 'To URL'", "% Identical"]]
	df = df.sort_values(["% Identical"], ascending = False)
	df["% Identical"] = df["% Identical"].multiply(100).round(2).astype(str) + '%'
	df = df.reset_index(drop=True)
	df.index = df.index + 1
	return df
#Main function end

#Streamlit logic
st.set_page_config(layout="wide", page_title="URL Mapping Tool")
st.title("***URL Mapping Tool***", anchor=None)
st.markdown("""Find identical URLs in a website migration. This is useful when you need to map out the pages from 'current' or 'old' domain to the 'new' domain.

Use this tool also as a content plagiarism checker across other domains. An App by Francis Angelo Reyes of [Lupage Digital](https://www.lupagedigital.com/?utm_source=streamlit&utm_medium=referral&utm_campaign=urlmapping)

To avoid errors, don't enter media files (ex, .com/logo.jpg)""")

urls_1 = st.text_area("Enter 'From URLs' here. Maximum of 60 URLs. Enter full URLs (ex, https://currentdomain.com/current-page)", height=200)
urls_1 = urls_1.split()
urls_2 = st.text_area("Enter 'To URLs' here. Maximum of 60 URLs. Enter full URLs (ex, https://newdomain.com/new-page)", height=200)
urls_2 = urls_2.split()
submit_button = st.button(label='Get Identical URLs')

if submit_button:
	if len(urls_1) == 0 or len(urls_2) == 0:
		st.warning("Please enter the URLs.")
	elif urls_1 == urls_2:
		st.warning("URLs should not be 100% the same. Please try again.")
	elif len(urls_1) > 60 or len(urls_2) > 60:
		st.warning("Upload a maximum of 60 URLs only in both fields.")
	else:
		df = get_similarities(urls_1, urls_2)
		st.table(df)
		csv = df.to_csv()
		b64 = base64.b64encode(csv.encode()).decode()
		st.markdown('### **⬇️ Download output CSV File **')
		href = f"""<a href="data:file/csv;base64,{b64}">Download CSV File</a> (Right-click and save as "filename.csv". Don't left-click.)"""
		st.markdown(href, unsafe_allow_html=True)
