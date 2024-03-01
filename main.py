import streamlit as st
import asyncio
from utils.chat_utils import upload_openai_file, create_run, list_files
from utils.assistant_utils import poll_run_status
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = None
if "file_ids" not in st.session_state:
    st.session_state["file_ids"] = []
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "file_names" not in st.session_state:
    st.session_state["file_names"] = []

async def main():
    """ Main function for PR Prophet """
    st.markdown("""
                <h3 style='text-align: center; color: #f6bd60;'>Social Media Master</h3>
                """, unsafe_allow_html=True)
    st.text("")
    # Create the file uploader in the sidebar
    st.sidebar.markdown(
        """<p style="font-weight:20px;">
        @Erik -- Upload one or multiple files here.  All of the files that
        you upload within a session should be tracked, so you can reference them in the chat without
        having to reload them.  If for some reason this does not seem to be the case, let me know.  A list of
        supported file types can be found
        <a href="https://platform.openai.com/docs/assistants/tools/supported-files">here</a>.</p>""",
        unsafe_allow_html=True)
    uploaded_files = st.sidebar.file_uploader("Upload a file", accept_multiple_files=True)
    if uploaded_files is not None:
        logger.info("File(s) uploaded")
        # Check to see if the file name has already been uploaded
        for file in uploaded_files:
            if file.name in st.session_state["file_names"]:
                st.sidebar.warning(f"File {file.name} already uploaded")
                # Remove the file from the list of uploaded files
                uploaded_files.remove(file)
        upload_file_button = st.sidebar.button("Upload file(s)")
        if upload_file_button:
            # Check to see if the file name has already been uploaded
            for file in uploaded_files:
                file_id = await upload_openai_file(file.read())
                st.session_state["file_ids"].append(file_id)
                st.session_state["file_names"].append(file.name)
                st.sidebar.success(f"File {file.name} uploaded successfully")
                logger.info(f"File {file.name} uploaded successfully")

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
        with st.spinner("Hang tight, I'm working on your request..."):
            # Generate the full response from the chat model
            response = create_run(
                message_content=prompt,
                file_ids=[file_id for file_id in st.session_state.file_ids] if st.session_state["file_ids"] else None,
                thread_id=st.session_state["thread_id"]
            )
            logger.info(f"Response: {response}")
            if response:
                run_id = response["run_id"]
                thread_id = response["thread_id"]

                answer = await poll_run_status(run_id=run_id, thread_id=thread_id)
                if answer:
                    # Add the assistant response to the chat history
                    st.session_state.messages.append({"role": "assistant", "content": answer["message"]})
                    message_placeholder.markdown(answer["message"])
                    if st.session_state.thread_id is None:
                        st.session_state["thread_id"] = response["thread_id"]
                    st.session_state["file_ids"] = []

if __name__ == "__main__":
    asyncio.run(main())
