# main.py
# from langchain import hub
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent

import streamlit as st
from tools_fin import FIR_extract, FIRrag
from langchain_groq import ChatGroq  
# from langgraph.prebuilt import create_react_agent 
# from langchain_community.llms import Ollama
import os
from datetime import date, time
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# tools = [FIRrag,FIR_extract]

# Ensure you have created a directory to store FIR PDFs
FIR_REPORTS_DIR = "FIR_reports"
os.makedirs(FIR_REPORTS_DIR, exist_ok=True)

# Dummy users for authentication
USER_CREDENTIALS = {
    "police": {"username": "police", "password": "police123", "role": "police"},
    "victim": {"username": "victim", "password": "victim123", "role": "victim"},
}

# Initialize session state for chat messages
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Define the login page
def login():
    st.title("FIR Assistant Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    user_role = None

    if st.button("Login"):
        for user, creds in USER_CREDENTIALS.items():
            if username == creds["username"] and password == creds["password"]:
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.session_state["role"] = creds["role"]
                st.success(f"Logged in as {creds['role'].capitalize()}")
                return
        st.error("Invalid credentials. Please try again.")

# Define the Police Dashboard
def police_dashboard():
    st.header("Police Dashboard")
    st.write("### FIR Statistics")
    # Placeholder for actual statistics and plots
    st.write("**Total FIRs Filed:** 150")
    st.write("**Pending FIRs:** 20")
    st.write("**Resolved FIRs:** 130")
    
    # Sample Plot (You can integrate real data and use plotly or matplotlib)
    st.write("### FIR Distribution by District")
    st.bar_chart({"Bandra": 50, "Andheri": 30, "Borivali": 20, "Colaba": 25, "Others": 25})

# Define the FIR Form Page
def fir_form():
    st.header("File a New FIR")
    with st.form("fir_form"):
        district = st.text_input("District")
        police_station = st.text_input("Police Station")
        fir_date = st.date_input("FIR Date", date.today())
        incident_date = st.date_input("Incident Date")
        incident_time = st.time_input("Incident Time")
        information_type = st.selectbox("Type of Information", ["Written", "Oral"])
        place_of_occurrence = st.text_input("Place of Occurrence")
        location_details = st.text_input("Location Details")
        complainant_name = st.text_input("Complainant Name")
        complainant_father_husband_name = st.text_input("Complainant's Father/Husband Name")
        complainant_dob = st.date_input("Complainant DOB")
        complainant_address = st.text_area("Complainant Address")
        accused_details = st.text_area("Accused Details (Separate multiple details by newline)").split("\n")
        delay_reason = st.text_area("Reason for Delay in Reporting")
        stolen_properties = st.text_area("Stolen Properties (Separate multiple items by comma)").split(",")
        
        submitted = st.form_submit_button("Submit FIR")
        
        if submitted:
            # Generate FIR PDF
            fir_number = f"FIR-{district[:3].upper()}-{len(os.listdir(FIR_REPORTS_DIR)) + 1}"
            pdf_path = os.path.join(FIR_REPORTS_DIR, f"{fir_number}.pdf")
            c = canvas.Canvas(pdf_path, pagesize=letter)
            width, height = letter
            
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 50, f"FIR Number: {fir_number}")
            c.drawString(50, height - 70, f"District: {district}")
            c.drawString(50, height - 90, f"Police Station: {police_station}")
            c.drawString(50, height - 110, f"FIR Date: {fir_date}")
            c.drawString(50, height - 130, f"Incident Date: {incident_date}")
            c.drawString(50, height - 150, f"Incident Time: {incident_time}")
            c.drawString(50, height - 170, f"Information Type: {information_type}")
            c.drawString(50, height - 190, f"Place of Occurrence: {place_of_occurrence}")
            c.drawString(50, height - 210, f"Location Details: {location_details}")
            c.drawString(50, height - 230, f"Complainant Name: {complainant_name}")
            c.drawString(50, height - 250, f"Complainant's Father/Husband Name: {complainant_father_husband_name}")
            c.drawString(50, height - 270, f"Complainant DOB: {complainant_dob}")
            c.drawString(50, height - 290, f"Complainant Address: {complainant_address}")
            c.drawString(50, height - 310, "Accused Details:")
            for i, detail in enumerate(accused_details, start=1):
                c.drawString(70, height - 310 - i*20, f"{i}. {detail}")
            c.drawString(50, height - 310 - (len(accused_details)+1)*20, f"Delay Reason: {delay_reason}")
            c.drawString(50, height - 330 - (len(accused_details)+1)*20, "Stolen Properties:")
            for i, prop in enumerate(stolen_properties, start=1):
                c.drawString(70, height - 330 - (len(accused_details)+1)*20 - i*20, f"{i}. {prop.strip()}")
            
            c.save()
            
            st.success(f"FIR filed successfully! FIR Number: {fir_number}")
            st.download_button(
                label="Download FIR PDF",
                data=open(pdf_path, "rb").read(),
                file_name=f"{fir_number}.pdf",
                mime="application/pdf"
            )

# Define the Chatbot Page for Police with Streamlit Chat Interface
def police_chatbot():
    st.header("FIR Chatbot")
    st.write("Describe the crime incident, and the chatbot will extract FIR details and relevant IPC sections.")

    # Chat Input
    user_input = st.chat_input("You: ")

    if user_input:
        # Append user message to the chat history
        st.session_state["messages"].append({"role": "user", "content": user_input})

        with st.spinner("Processing..."):
            try: 
                
                tools = [FIRrag,FIR_extract]
                
                prompt = hub.pull("hwchase17/react") 
                prompt.template += "For the user query use FIRrag and FIR_extract to generate the required FIR report"
                # print(prompt) 
                # print(user_input)
                # # # Create the agent 

                agent = create_react_agent(llm, tools, prompt)  



                agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True) 
                # response = agent_executor.invoke({"input": user_input}) 
                # print(response)
                # Extract FIR details
                fir_entities = FIR_extract.invoke(user_input)
                # Retrieve IPC sections
                ipc_sections = FIRrag.invoke(user_input)

                # Append assistant responses to the chat history
                st.session_state["messages"].append({"role": "assistant", "content": fir_entities})
                st.session_state["messages"].append({"role": "assistant", "content": f"**Relevant IPC Sections and Acts:**\n{ipc_sections}"})
            except Exception as e:
                st.session_state["messages"].append({"role": "assistant", "content": f"**Error:** {str(e)}"})

        # Display the conversation
        for message in st.session_state["messages"]:
            if message["role"] == "user":
                st.chat_message("user").write(message["content"])
            else:
                st.chat_message("assistant").write(message["content"])

# Define the IPC Catalog Page for Police
def ipc_catalog():
    st.header("IPC Catalog Search")
    search_query = st.text_input("Search IPC Sections:")

    if st.button("Search"):
        if search_query:
            with st.spinner("Searching for relevant IPC sections..."):
                
                st.subheader("Search Results:")
                # st.write(ipc_results)
        else:
            st.warning("Please enter a search query.")

# Define the Victim Dashboard
def victim_dashboard():
    st.header("Victim Dashboard")
    st.write("### FIR Tracking Details")
    # Placeholder for actual tracking details
    st.write("**FIR Number:** FIR-BAN-1")
    st.write("**Status:** Under Investigation")
    st.write("**Filed On:** 2024-09-15")
    
    # Sample Plot
    st.write("### FIR Status Distribution")
    st.bar_chart({"Under Investigation": 1, "Resolved": 0, "Pending": 0})

# Define the Proof Page for Victim
def proof_page():
    st.header("FIR Proof")
    fir_number = st.text_input("Enter FIR Number to View Proof:")

    if st.button("View Proof"):
        if fir_number:
            pdf_path = os.path.join(FIR_REPORTS_DIR, f"{fir_number}.pdf")
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    PDFbyte = f.read()
                st.download_button(
                    label="Download FIR PDF",
                    data=PDFbyte,
                    file_name=f"{fir_number}.pdf",
                    mime="application/pdf"
                )
                st.markdown(f"**FIR Number:** {fir_number}")
                st.write("**Download the FIR PDF using the button above.**")
            else:
                st.error("FIR not found. Please check the FIR number and try again.")
        else:
            st.warning("Please enter an FIR number.")

# Define the main function
def main():
    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["username"] = ""
        st.session_state["role"] = ""
    
    if not st.session_state["authenticated"]:
        login()
    else:
        if st.session_state["role"] == "police":
            # Sidebar for Police
            st.sidebar.title("Police Panel")
            page = st.sidebar.radio("Navigate to", ["Dashboard", "FIR Form", "Chatbot", "IPC Catalog", "Logout"])
            
            if page == "Dashboard":
                police_dashboard()
            elif page == "FIR Form":
                fir_form()
            elif page == "Chatbot":
                police_chatbot()
            elif page == "IPC Catalog":
                ipc_catalog()
            elif page == "Logout":
                st.session_state["authenticated"] = False
                st.session_state["messages"] = []
                st.experimental_rerun()
        
        elif st.session_state["role"] == "victim":
            # Sidebar for Victim
            st.sidebar.title("Victim Panel")
            page = st.sidebar.radio("Navigate to", ["Dashboard", "Proof", "Logout"])
            
            if page == "Dashboard":
                victim_dashboard()
            elif page == "Proof":
                proof_page()
            elif page == "Logout":
                st.session_state["authenticated"] = False
                st.session_state["messages"] = []
                st.experimental_rerun()

if __name__ == "__main__":
    main()
