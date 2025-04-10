from dotenv import load_dotenv
import os
import streamlit as st
import requests
from google import genai
from google.genai import types

# Load environment variables from .env file
load_dotenv()

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './sqy-prod.json'

# Initialize Gemini client
gemini_client = genai.Client(
    http_options=types.HttpOptions(api_version="v1beta1"),
    vertexai=True,
    project='sqy-prod',
    location='us-central1'
)

gemini_tools = [types.Tool(google_search=types.GoogleSearch())]

# Centralized content creation function for Gemini (Undefined Template)
def create_content_locality_description(prompt: str, city: str, locality: str) -> str:
    try:
        # Preprocess city and locality for the URL
        city_lower = city.lower()
        locality_processed = locality.lower().replace(' ', '-')
        url = f"https://www.squareyards.com/getlocalitydatafordesc/{city_lower}/{locality_processed}"
        
        # Update the prompt with the preprocessed URL
        full_query = prompt.format(locality=locality, city=city, url=url)
        print(full_query)
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=full_query,
            config=types.GenerateContentConfig(
                tools=gemini_tools,
                max_output_tokens=8192,
                system_instruction="You are a helpful real-estate agent. I want response in proper tags and please direct give response dont mention any suggestion line or note. You may include additional useful details from Google search like PAA or pincode.",
                temperature=0.7,
            )
        )
        content = response.text
        return content.replace("\n", "")
    except Exception as e:
        return f"Error generating content: {str(e)}"

# Streamlit App
def main():
    st.title("Locality Description Generator")
    st.write("Generate detailed locality descriptions using Gemini AI")

    # Default prompt with {url} placeholder
    default_prompt = """
    Provide a detailed description for {locality}, {city}. 
    Utilize data from "{url}" and incorporate trending "People Also Ask" (PAA) and "People Also Search For" data.
    The description should cover:
    - About locality brief simple description (Don't mention community)
    - Location and connectivity (metro, roads, proximity to business hubs)
    - Lifestyle and livability (amenities, green spaces, safety)
    - Entertainment and amenities (shopping, restaurants, recreation)
    - Education and healthcare (schools, hospitals)
    - Property rates and price trends
    - Real estate builders and projects (newly launched, ready to move)
    - Advantages and disadvantages
    - Future prospects
    - FAQs based on PAA (People Also Ask)
    - Use simple, natural, realistic language without embellishment.
    - I want response in proper tags, dont add any special character and please direct give response dont mention any suggestion line or note.
    Use bullet points and tables where appropriate. 
    ### **Response Format should be this:**
    The heading should be in <h2> heading </h2> for each section and paragraph should be in <p> paragraph </p>, I use your response directly on my UI, so give response according to UI.
    <h2>People Also Ask</h2>
    <div class="panel">
        <div class="panelHeader">
            <strong>Q: [Your Question Here]</strong>
            <em class="icon-arrow-down"></em>
        </div>
        <div class="panelBody">
            <p>[Your Answer Here]</p>
        </div>
    </div>
    """

    # Input form
    with st.form(key='locality_form'):
        city = st.text_input("City", "")
        locality = st.text_input("Locality", "")
        prompt = st.text_area("Edit Prompt", default_prompt, height=400)
        submit_button = st.form_submit_button(label='Generate Description')

    if submit_button and city and locality:
        with st.spinner("Generating locality description..."):
            # Fetch locality data (optional, kept for context)
            api_url = f"https://stage-www.squareyards.com/getlocalitydatafordesc/{city.lower()}/{locality.lower().replace(' ', '-')}"
            response = requests.get(api_url)
            # print(response.status_code)
            if response.status_code != 200:
                st.error("Failed to fetch locality data")
                return

            # Generate the full description using the user-editable prompt
            full_description = create_content_locality_description(prompt, city, locality)
            st.markdown(full_description, unsafe_allow_html=True)

if __name__ == "__main__":
    main()