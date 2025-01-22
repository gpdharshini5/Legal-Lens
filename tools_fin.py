from langchain.chains import create_retrieval_chain 
from langchain.chains.combine_documents import create_stuff_documents_chain 
from langchain_core.tools import tool 
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv  
import os 
from pydantic import BaseModel, Field
from typing import Optional, List 
from langchain_groq import ChatGroq 
from langchain_community.embeddings import OllamaEmbeddings 
from langchain_community.vectorstores import FAISS
from datetime import date, time
from langchain_core.prompts import ChatPromptTemplate

load_dotenv() 

groq_key = "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"  # Ensure this is set in your .env file

llm = ChatGroq(groq_api_key=groq_key, model="llama3-8b-8192") 

class FIRDetails(BaseModel):
    district: str = Field(description="District where the FIR is being registered.")
    police_station: str = Field(description="Police station where the FIR is being filed.")
    fir_date: date = Field(description="Date when the FIR is registered.")
    
    # Occurrence of Offense
    incident_date: Optional[date] = Field(None, description="Date when the incident occurred.")
    incident_time: Optional[time] = Field(None, description="Time when the incident occurred.")
    
    information_type: Optional[str] = Field(None, description="Type of information provided (Written/Oral).")
    
    # Place of Occurrence
    place_of_occurrence: Optional[str] = Field(None, description="Place where the offense occurred.")
    location_details: Optional[str] = Field(None, description="Detailed location information (if available).")
    
    # Complainant's Information
    complainant_name: Optional[str] = Field(None, description="Name of the complainant.")
    complainant_father_husband_name: Optional[str] = Field(None, description="Complainant's father or husband's name.")
    complainant_dob: Optional[str] = Field(None, description="Date of birth of the complainant.")
    complainant_address: Optional[str] = Field(None, description="Complainant's full address.")
    
    # Accused Details
    accused_details: Optional[List[str]] = Field(None, description="Details of the accused persons involved.")
    
    # Reasons for Delay
    delay_reason: Optional[str] = Field(None, description="Reasons for delay in reporting the incident.")
    
    # Property Details
    stolen_properties: Optional[List[str]] = Field(None, description="Particulars of properties stolen or involved in the crime.")

@tool 
def FIR_extract(query: str):
    """Expert in extraction of entities related to crime incidents. Use this for any crime incident. Input query is the string of crime incident."""
    parser = PydanticOutputParser(pydantic_object=FIRDetails)

    prompt = PromptTemplate(
        template=(
            "Extract the following entities from the incident description:\n"
            "- District\n- Police Station\n- FIR Date\n"
            "- Incident Date\n- Incident Time\n- Information Type\n"
            "- Place of Occurrence\n- Location Details\n- Complainant Name\n"
            "- Complainant's Father/Husband Name\n- Complainant DOB\n"
            "- Complainant Address\n- Accused Details\n- Delay Reason\n"
            "- Stolen Properties\n\n"
            "{query}\n\n{format_instructions}"
        ),
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | llm | parser
    return chain.invoke({"query": query})

@tool 
def FIRrag(query: str):
    """Expert in finding the IPC and sections based on the crime or case incident. Input is the case incident given by the user."""
    embeddings = OllamaEmbeddings(model='nomic-embed-text') 
    
    # Load the FAISS vector store
    db = FAISS.load_local("/home/adhishsekar/Documents/POC/Justice/law_index", embeddings, allow_dangerous_deserialization=True)
    
    # Define the RAG prompt
    prompt = """Use the following pieces of context to answer the question at the end.
You will be given a case incident as a question based on the context and question find the required IPC and sections from the context

<context>
{context} 
</context>

Question: {input}

Helpful Answer:"""
    custom_rag_prompt = ChatPromptTemplate.from_template(prompt)
    
    # Create the document chain
    document_chain = create_stuff_documents_chain(llm, custom_rag_prompt)
    retriever=db.as_retriever()
    # Create the retrieval chain
    retriever_chain = create_retrieval_chain(retriever,document_chain)
    
    # Perform the retrieval and generation
    response = retriever_chain.invoke({"input": query})
    return response['answer']
