from dotenv import load_dotenv
import os
import random
import streamlit as st
import requests
import pyperclip
import re
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

# --- Locality Description Function ---
def create_content_locality_description(prompt: str, city: str, locality: str) -> str:
    try:
        city_lower = city.lower()
        locality_processed = locality.lower().replace(' ', '-')
        url = f"https://www.squareyards.com/getlocalitydatafordesc/{city_lower}/{locality_processed}"
        full_query = prompt.format(locality=locality, city=city, url=url)
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

def create_content_listing_description_format():
    font_list = [    
                    "The response format should be flexible—either a single paragraph, format:(<p>.....</p>) or a mix of one paragraph with 2–3 meaningful bullet points,format:(<ul> <li>...</li></ul>), depending on what best suits the data.",
                    "The response format should be flexible—either a single or double paragraph in this format (<p>.....</p>)",
                    "The response format should be a single paragraph in this format (<p>.....</p>)" 
                ]
    selected_font = random.choice(font_list)
    return selected_font
    
# --- Listing Description Function ---
def create_content_listing_description(prompt: str, metadata: str) -> str:
    try:
        full_query = prompt.format(metadata=metadata,select_font=create_content_listing_description_format())
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=full_query,
            config=types.GenerateContentConfig(
                max_output_tokens=2048,
                system_instruction="You are a helpful real-estate agent. Please direct give response dont mention any suggestion line or note. Use simple, natural, and realistic language.",
                temperature=0.7,
            )
        )
        content = response.text
        content = content.replace("```html", "").replace("```", "").replace("-"," ").replace("*","")
        return content.replace("\n", "")
    except Exception as e:
        return f"Error generating listing description: {str(e)}"

# --- Translation Functions ---
def get_project_data(project_id):
    api_url = f"https://www.squareyards.com/project-data-for-ai/{project_id}"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        raise ValueError(f"Failed to fetch data for project ID {project_id}. Status code: {response.status_code}")

def translate_text(text: str, target_language: str) -> str:
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=f"""You are a professional translator specialized in real estate content.
            Your task is to translate English text into {target_language}, preserving accuracy and domain relevance.

            If the input is a key–value structure (such as JSON), translate only the values while keeping all keys unchanged.

            Maintain the original structure and formatting in your response.

            Do not skip any values — every translatable value must be translated.

            Retain real estate–specific terms (e.g., "BHK", "Cr", "Possession") in English when appropriate.

            Do not add explanations, comments, or extra output — return only the translated content.

            Begin by translating the following English input to {target_language}:

            "{text}"
            """,
            config=types.GenerateContentConfig(
                max_output_tokens=3024,
                temperature=1,
            )
        )
        return response.text.strip().replace('"', '')
    except Exception as e:
        return f"Error translating text: {str(e)}"

# --- Streamlit App ---
def main():
    st.title("Real Estate Content Generator & Translator")
    st.write("Generate locality/listing descriptions or translate project data into Hindi/Marathi")

    # Mode selection
    mode = st.radio("Choose Functionality:", ["Locality Description", "Listing Description", "Text Translator"], index=0)

    # Default prompt for locality description
    default_locality_prompt = """
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

    # Default prompt for listing description
    default_listing_prompt = """
    You are a specialized assistant designed to generate concise and appealing property listing descriptions for real estate. Based on the provided property metadata:

    Output Requirements:
    - Format the output in clean, structured HTML that matches the specified template
    - Mention lifestyle benefits (spacious living, modern design, natural light)
    - Exclude city or locality details.
    - Output response should be like human generated so no fancy or repetitive words.
    - Base the output strictly on the provided data
    - {select_font}

    Important Notes:
    - Do not include any introductory or explanatory text in your response
    - Direct return response, do not add any suggestions, notes, or additional commentary
    - Keep the description human written like a beginner and simaple natural
    
    Generate a property listing description based on the following metadata: {metadata}
    """

    if mode == "Locality Description":
        st.header("Locality Description Generator")
        with st.form(key='locality_form'):
            city = st.text_input("City", "")
            locality = st.text_input("Locality", "")
            prompt = st.text_area("Edit Locality Prompt", default_locality_prompt, height=400)
            submit_button = st.form_submit_button(label='Generate Locality Description')

        if submit_button and city and locality:
            with st.spinner("Generating locality description..."):
                api_url = f"https://www.squareyards.com/getlocalitydatafordesc/{city.lower()}/{locality.lower().replace(' ', '-')}"
                response = requests.get(api_url)
                if response.status_code != 200:
                    st.error("Failed to fetch locality data")
                    return
                full_description = create_content_locality_description(prompt, city, locality)
                st.markdown(full_description, unsafe_allow_html=True)

                if st.button("Copy Description to Clipboard"):
                    pyperclip.copy(full_description)
                    st.success("Description copied to clipboard!")
                
                st.download_button(
                    label="Download Description",
                    data=full_description,
                    file_name=f"{locality}_{city}_description.html",
                    mime="text/html"
                )

    elif mode == "Listing Description":
        st.header("Listing Description Generator")
        with st.form(key='listing_form'):
            metadata = st.text_input('Property Metadata (e.g., "listingType": "Sale", "descKeywords": "Schools in vicinity,Peaceful Vicinity,Affordable,Vastu compliant,Prime Location", "totalPrice": "17000000", "availArea": "1501", "areaInSqft": 1501, "areaUOMId": "22", "propertyName": "Apartment", "cityName": "Kolkata", "localityName": "Hazra Road", "projectName": "Fort Oasis", "unitNo": "6", "Possession_Status": "Ready To Move", "Furnishing_Status": "Unfurnished", "Number_of_Rooms": 3, "Number_of_Bathroom": 3, "views": "Garden View", "coverdParking": 1, "floor_no": "2", "tower": "4", "total_floor": "9", "amenities": ["Badminton Court(s)", "Attached Market", "24 x 7 Security", "Balcony", "Visitors Parking", "ATMs", "View of Water", "View of Landmark", "Walk-in Closet", "Waste Disposal"])', "")
            prompt = st.text_area("Edit Listing Prompt", default_listing_prompt, height=400)
            submit_button = st.form_submit_button(label='Generate Listing Description')

        if submit_button and metadata:
            with st.spinner("Generating listing description..."):
                listing_description = create_content_listing_description(prompt, metadata)
                st.markdown(listing_description, unsafe_allow_html=True)

                if st.button("Copy Description to Clipboard"):
                    pyperclip.copy(listing_description)
                    st.success("Description copied to clipboard!")
                
                st.download_button(
                    label="Download Description",
                    data=listing_description,
                    file_name="listing_description.html",
                    mime="text/html"
                )

    else:
        st.header("Text Translator (English → Hindi/Marathi)")
        language_option = st.selectbox("Select Target Language:", ["Hindi", "Marathi"])
        target_lang_code = "hi" if language_option == "Hindi" else "mr"

        project_id = st.text_input("Enter Project ID:", "308832")
        
        if st.button("Fetch and Translate"):
            try:
                input_json = get_project_data(project_id)
                input_text = (input_json)
                st.subheader("Extracted Data:")
                st.write(input_text)
                translated = translate_text(input_text, target_lang_code)
                
                st.subheader("Translated Text:")
                st.write(translated)

                if st.button("Copy to Clipboard"):
                    pyperclip.copy(translated)
                    st.success("Translated text copied to clipboard!")
                
                st.download_button(
                    label="Download Translated Text",
                    data=translated,
                    file_name=f"translated_{project_id}_{target_lang_code}.txt",
                    mime="text/plain"
                )

            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"An error occurred during translation: {str(e)}")

if __name__ == "__main__":
    main()
