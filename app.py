from classes import Page
from polyfuzz import PolyFuzz
import base64
import pandas as pd
import streamlit as st

#Function start
def get_similarities():
	content_list_1 = [Page(url).content() for url in urls_1]
	content_list_2 = [Page(url).content() for url in urls_2]
  
#Create a dictionary for 2nd content list "url":"content"
	content_dictionary = {urls_2[i]: content_list_2[i] for i in range(len(urls_2))}

#Polyfuzz library start
	model = PolyFuzz("TF-IDF")
	model.match(content_list_1, content_list_2)

	data = model.get_matches()

#Map the content result to urls
	def get_key(val):
		for key, value in content_dictionary.items():
			if val == value:
				return key
		return "key doesn't exist"
	result = list(map(get_key, data["To"]))

#Dataframe creation
	to_zip = zip(urls_1, result, data["Similarity"])
	df = pd.DataFrame(to_zip)
	df.columns = ["From URL", "To URL", "% Identical"]
	page_title_from = [Page(element).page_title() for element in df["From URL"]]
	df["Page Title of 'From URL'"] = page_title_from
	page_title_to = [Page(element).page_title() for element in df["To URL"]]
	df["Page Title of 'To URL'"] = page_title_to
	df = df[["From URL", "Page Title of 'From URL'", "To URL", "Page Title of 'To URL'", "% Identical"]]
	df = df.sort_values(["% Identical"], ascending =False)
	df["% Identical"] = [element*100 for element in df["% Identical"]]
	df["% Identical"] = [str("{:.2f}".format(element))+"%" for element in df["% Identical"]]
	df = df.reset_index(drop=True)
	df.index = df.index + 1
	return df
#Function end

#Streamlit logic
st.set_page_config(layout="wide", page_title="URL Mapping Tool")
st.title("***URL Mapping Tool***", anchor=None)
st.markdown("""Find identical URLs in a website migration. This is useful when you need to map out the pages from 'current' or 'old' domain to the 'new' domain.

Use this tool as a content quick plagiarism checker as well.""")

urls_1 = st.text_area("Add 'From URLs' here. Maximum of 100 URLs. Input Full URLs (ex. https://currentdomain.com/current-page)", height=200)
urls_1 = urls_1.split()
urls_2 = st.text_area("Add 'To URLs' here. Maximum of 100 URLs. Input Full URLs (ex. https://newdomain.com/new-page)", height=200)
urls_2 = urls_2.split()
submit_button = st.button(label='Get Identical URLs')

if submit_button:
	if len(urls_1) > 100 or len(urls_2) > 100:
		st.warning("Upload a maximum of 100 URLs only for both fields.")
	else:
		df = get_similarities()
		st.table(df)
		csv = df.to_csv()
		b64 = base64.b64encode(csv.encode()).decode()
		st.markdown('### **⬇️ Download output CSV File **')
		href = f"""<a href="data:file/csv;base64,{b64}">Download CSV File</a> (Right-click and save as "filename.csv". Don't left-click.)"""
		st.markdown(href, unsafe_allow_html=True)