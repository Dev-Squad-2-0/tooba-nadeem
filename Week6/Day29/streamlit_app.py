import uuid

import requests
import streamlit as st


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

API_URL = "http://127.0.0.1:8000/chat"


# -------------------------------------------------------------------
# Page configuration
# -------------------------------------------------------------------

st.set_page_config(
    page_title="AFL Assistant",
    page_icon="🏉",
    layout="centered",
)


# -------------------------------------------------------------------
# Session state
# -------------------------------------------------------------------

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = (
        f"streamlit-{uuid.uuid4().hex[:8]}"
    )

if "messages" not in st.session_state:
    st.session_state.messages = []


# -------------------------------------------------------------------
# Header
# -------------------------------------------------------------------

st.title("🏉 AFL Assistant")

st.caption(
    "Ask about AFL teams, players, statistics, matches, "
    "and model-based predictions."
)


# -------------------------------------------------------------------
# Sidebar
# -------------------------------------------------------------------

with st.sidebar:
    st.header("About")

    st.write(
        "This interface connects to the AFL assistant "
        "through the FastAPI /chat endpoint."
    )

    st.write("**Capabilities**")
    st.write("• AFL factual questions")
    st.write("• Historical/statistical retrieval")
    st.write("• Match-winner predictions")
    st.write("• Top-player predictions")
    st.write("• AFL-only scope guardrails")

    st.divider()

    if st.button("New conversation"):
        st.session_state.conversation_id = (
            f"streamlit-{uuid.uuid4().hex[:8]}"
        )
        st.session_state.messages = []
        st.rerun()

    st.caption(
        f"Conversation: {st.session_state.conversation_id}"
    )


# -------------------------------------------------------------------
# Display previous messages
# -------------------------------------------------------------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        metadata = message.get("metadata")

        if metadata:
            with st.expander("Prediction / API details"):
                st.json(metadata)


# -------------------------------------------------------------------
# Chat input
# -------------------------------------------------------------------

user_message = st.chat_input(
    "Ask an AFL question..."
)


if user_message:

    # ---------------------------------------------------------------
    # Display user message
    # ---------------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    with st.chat_message("user"):
        st.markdown(user_message)

    # ---------------------------------------------------------------
    # Call FastAPI
    # ---------------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            try:
                response = requests.post(
                    API_URL,
                    json={
                        "message": user_message,
                        "conversation_id": (
                            st.session_state.conversation_id
                        ),
                    },
                    timeout=30,
                )

                response.raise_for_status()

                data = response.json()

                assistant_response = data.get(
                    "response",
                    "The API returned no response.",
                )

                st.markdown(assistant_response)

                # ---------------------------------------------------
                # Show useful API metadata
                # ---------------------------------------------------

                metadata = data.get("prediction_metadata")

                if metadata:
                    with st.expander("Prediction / API details"):
                        st.json(metadata)

                # ---------------------------------------------------
                # Store assistant response
                # ---------------------------------------------------

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_response,
                        "metadata": metadata,
                    }
                )

            except requests.exceptions.Timeout:
                error_message = (
                    "The AFL assistant took too long to respond. "
                    "Please try again."
                )

                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                    }
                )

            except requests.exceptions.ConnectionError:
                error_message = (
                    "I couldn't connect to the FastAPI server. "
                    "Make sure the API is running with:\n\n"
                    "`uvicorn main:app --reload`"
                )

                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                    }
                )

            except requests.exceptions.HTTPError as exc:
                error_message = (
                    f"The API returned an HTTP error: {exc}"
                )

                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                    }
                )

            except Exception as exc:
                error_message = (
                    f"Unexpected error while contacting the API: "
                    f"{exc}"
                )

                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                    }
                )