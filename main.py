import streamlit as st
import asyncio
from utils.chat_utils import upload_openai_file, create_run
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = None
if "file_id" not in st.session_state:
    st.session_state["file_id"] = None
if "messages" not in st.session_state:
    st.session_state["messages"] = []

async def main():
    """ Main function for PR Prophet """
    st.markdown("""
                <h3 style='text-align: center; color: #f6bd60;'>Social Media Master</h3>
                """, unsafe_allow_html=True)
    st.text("")
    # Create the file uploader in the sidebar
    uploaded_file = st.sidebar.file_uploader("Upload a file")
    if uploaded_file is not None:
        logger.info("File uploaded")
        upload_file_button = st.sidebar.button("Upload file")
        if upload_file_button:
            file_id = await upload_openai_file(
                file=uploaded_file.getvalue()
            )
            st.session_state["file_id"] = file_id

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        if message["role"] == "assistant":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        elif message["role"] == "user":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("How can I help you today?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()

        # Generate the full response from the chat model
        response = create_run(
            message_content=prompt,
            file_ids=[st.session_state["file_id"]] if st.session_state["file_id"] else None,
            thread_id=st.session_state["thread_id"]
        )
        if st.session_state.thread_id is None:
            st.session_state["thread_id"] = response["thread_id"]
        message_placeholder.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    asyncio.run(main())
