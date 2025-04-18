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

# Centralized content creation function for Gemini (Locality Description)
def create_content_locality_description(prompt: str, city: str, locality: str) -> str:
    try:
        # Preprocess city and locality for the URL
        city_lower = city.lower()
        locality_processed = locality.lower().replace(' ', '-')
        url = f"https://www.squareyards.com/getlocalitydatafordesc/{city_lower}/{locality_processed}"
        
        # Update the prompt with the preprocessed URL
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

# New function for generating listing description
def create_content_listing_description(prompt: str, metadata: str) -> str:
    try:
        # Update the prompt with the metadata
        full_query = prompt.format(metadata=metadata)
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
        return content.replace("\n", "")
    except Exception as e:
        return f"Error generating listing description: {str(e)}"

# Streamlit App
def main():
    st.title("Real Estate Description Generator")
    st.write("Generate detailed locality or listing descriptions using Gemini AI")

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

    # New prompt for listing description
    default_listing_prompt = """
    

    
    You are a specialized assistant designed to generate concise and appealing property listing descriptions. When a user provides property metadata, you will:
    1. Format the output in clean, structured HTML that matches the specified template
    2. Provide the response directly without any introductory text or suggestions
    3. Focus only on the most important  amenities, keeping descriptions brief and relevant for buyers/renters
    4. The response should be SEO-friendly
    5. Cover all the points provided in the key-value pairs of the metadata.

    Output Requirements:
    - Highlight key property features (price, size, configuration, furnishings, amenities)
    - Mention lifestyle benefits (spacious living, modern design, natural light)
    - Exclude city or locality details
    - Contain no special characters
    - Be presented either as 1-2 paragraphs 
    - Begin immediately with the HTML content (no introductory text or notes)
    - Choose either only 2 paragraphs OR both paragrapgh and bullet points(2-4 only) based on what best suits the metadata

    HTML Format Template:
    For paragraphs:
    <p>Property description paragraph with key features and benefits.</p>
    <p>Additional property description if needed.</p>
    
    For bullet points(bullets point should be a full meaningful sentence, not just a phrase):
    <ul>
    <li>Key property feature or benefit point</li>
    <li>Additional property feature or benefit point</li>
    </ul>
    
    Important Notes:
    - Do not include any introductory or explanatory text in your response
    - Start directly with the HTML content
    - Ensure all HTML tags are properly closed and formatted
    - Do not add any suggestions, notes, or additional commentary
    - Keep the description concise, natural, and focused on property features and benefits
    
    Generate a property listing description based on the following metadata: {metadata}


"""
#     default_listing_prompt = """
#     Generate a concise and appealing property listing description based on the following metadata: {metadata}.
#     The description should:
#     - Highlight key property features (e.g., size, configuration, furnishings, amenities like balcony or parking).
#     - Mention lifestyle benefits (e.g., spacious living, modern design, natural light).
#     - Include a call-to-action (e.g., "Contact us to schedule a viewing!").
#     - Exclude city or locality details.
#     - Use simple, natural, and realistic language without embellishment.
#     - Dont add any special character and please direct give response dont mention any suggestion line or note.
# """
    # ### **Response Format should be this:**
    # The heading should be in <h2> heading </h2> and paragraph should be in <p> paragraph </p>, I use your response directly on my UI, so give response according to UI.
    # <h2>Property Overview</h2>
    # <p>[Description here]</p>
    # <h2>Key Features</h2>
    # <ul>
    #     <li>[Feature 1]</li>
    #     <li>[Feature 2]</li>
    # </ul>
    # <h2>Contact Us</h2>
    # <p>[Call-to-action here]</p>"""
 

    # Selection for description type
    description_type = st.radio("Select Description Type", ("Locality Description", "Listing Description"))

    if description_type == "Locality Description":
        # Input form for locality description
        with st.form(key='locality_form'):
            city = st.text_input("City", "")
            locality = st.text_input("Locality", "")
            prompt = st.text_area("Edit Locality Prompt", default_locality_prompt, height=400)
            submit_button = st.form_submit_button(label='Generate Locality Description')

        if submit_button and city and locality:
            with st.spinner("Generating locality description..."):
                # Fetch locality data
                api_url = f"https://stage-www.squareyards.com/getlocalitydatafordesc/{city.lower()}/{locality.lower().replace(' ', '-')}"
                response = requests.get(api_url)
                if response.status_code != 200:
                    st.error("Failed to fetch locality data")
                    return

                # Generate the locality description
                full_description = create_content_locality_description(prompt, city, locality)
                st.markdown(full_description, unsafe_allow_html=True)

    else:
        # Input form for listing description
        with st.form(key='listing_form'):
            metadata = st.text_input('Property Metadata (e.g., "listingType": "Sale", "descKeywords": "Schools in vicinity,Peaceful Vicinity,Affordable,Vastu compliant,Prime Location", "totalPrice": "17000000", "availArea": "1501", "areaInSqft": 1501, "areaUOMId": "22", "propertyName": "Apartment", "cityName": "Kolkata", "localityName": "Hazra Road", "projectName": "Fort Oasis", "unitNo": "6", "Possession_Status": "Ready To Move", "Furnishing_Status": "Unfurnished", "Number_of_Rooms": 3, "Number_of_Bathroom": 3, "views": "Garden View", "coverdParking": 1, "floor_no": "2", "tower": "4", "total_floor": "9", "amenities": ["Badminton Court(s)", "Attached Market", "24 x 7 Security", "Balcony", "Visitors Parking", "ATMs", "View of Water", "View of Landmark", "Walk-in Closet", "Waste Disposal"])', "")
            # metadata = st.text_input("property_data {"listingType": "Sale", "descKeywords": "Schools in vicinity,Peaceful Vicinity,Affordable,Vastu compliant,Prime Location", "totalPrice": "17000000", "availArea": "1501", "areaInSqft": 1501, "areaUOMId": "22", "propertyName": "Apartment", "cityName": "Kolkata", "localityName": "Hazra Road", "projectName": "Fort Oasis", "unitNo": "6", "Possession_Status": "Ready To Move", "Furnishing_Status": "Unfurnished", "Number_of_Rooms": 3, "Number_of_Bathroom": 3, "views": "Garden View", "coverdParking": 1, "floor_no": "2", "tower": "4", "total_floor": "9", "amenities": ["Badminton Court(s)", "Attached Market", "24 x 7 Security", "Balcony", "Visitors Parking", "ATMs", "View of Water", "View of Landmark", "Walk-in Closet", "Waste Disposal"]}')

            prompt = st.text_area("Edit Listing Prompt", default_listing_prompt, height=400)
            submit_button = st.form_submit_button(label='Generate Listing Description')

        if submit_button and metadata:
            with st.spinner("Generating listing description..."):
                # Generate the listing description
                listing_description = create_content_listing_description(prompt, metadata)
                print(listing_description)
                listing_description  = listing_description.replace("```html","")
                listing_description  = listing_description.replace("```","")
                st.markdown(listing_description, unsafe_allow_html=True)

if __name__ == "__main__":
    main()