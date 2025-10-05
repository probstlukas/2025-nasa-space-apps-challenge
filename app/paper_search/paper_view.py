import html
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import networkx as nx
import streamlit as st
import streamlit.components.v1 as components

from utils import paper_chat
import utils.resource_manager as R
from utils.similarity_graph import get_similarity_graph


def setup_paper_view(resource_id: int, resource: R.PaperResource):

    st.header(f"📘 {resource.title}")

    tabs = st.tabs(
        [
            "Overview",
            "Read Paper",
            "Relevant Work",
            "Experiments",
            "Referenced Work",
            "Q&A",
        ]
    )

    (overview_tab, read_tab, relevant_work_tab, experiments_tab, references_tab, qa_tab) = (
        tabs
    )

    paper_url = resource.paper_url
    pdf_url = resource.pdf_url
    abstract = resource.abstract
    title = resource.title

    with overview_tab:
        authors = resource.authors
        year = resource.year
        infos = [str(year)]
        if authors is not None:
            infos.append(", ".join(authors))

        st.write(" • ".join(infos))

        if paper_url:
            url_label, primary_link = paper_url
            st.markdown(
                f"[View on {url_label}]({primary_link}) &emsp; [View PDF]({pdf_url})"
            )

        with st.container(border=True):
            st.markdown("#### Abstract")
            if abstract:
                st.write(abstract)
            else:
                st.info("No abstract available for this work.")

    pdf_bytes_key = f"paper_pdf_bytes_{resource_id}"

    with read_tab:
        st.subheader("Read the Paper")
        pdf_bytes: Optional[bytes] = st.session_state.get(pdf_bytes_key)

        if pdf_bytes is None and pdf_url:
            with st.spinner("Loading PDF viewer..."):
                pdf_bytes = paper_chat.fetch_pdf_bytes(pdf_url)
            st.session_state[pdf_bytes_key] = pdf_bytes

        if pdf_bytes:
            try:
                st.pdf(pdf_bytes, height=850)
            except Exception:
                st.warning(
                    "Inline PDF viewer unavailable. Use the links below instead."
                )
                if pdf_url:
                    components.iframe(pdf_url, height=850)
        if pdf_url:
            st.markdown(f"[Open PDF in new tab]({pdf_url})")
        if not pdf_url:
            st.info("No PDF link detected for this work.")

    with relevant_work_tab:
        st.subheader("Citation Graph")
        graph = get_similarity_graph()
        if resource_id not in graph:
            st.info("No citation relationships found for this paper yet.")
        else:
            neighbors = []
            for nbr in graph.neighbors(resource_id):
                data = graph[resource_id][nbr]
                similarity = float(data.get("similarity", 0.0))
                neighbors.append((nbr, similarity))
            neighbors.sort(key=lambda item: item[1], reverse=True)

            if not neighbors:
                st.info("This paper currently has no related entries in the citation graph.")
            else:
                top_neighbors = neighbors[:10]

                # Visualise ego graph (paper + top neighbours)
                subgraph_nodes = [resource_id] + [node for node, _ in top_neighbors]
                subgraph = graph.subgraph(subgraph_nodes).copy()

                pos = nx.spring_layout(subgraph, seed=42)
                fig, ax = plt.subplots(figsize=(6, 4))
                node_colors = ["#ff6b6b" if node == resource_id else "#4d96ff" for node in subgraph]
                nx.draw_networkx_nodes(
                    subgraph,
                    pos,
                    node_color=node_colors,
                    ax=ax,
                    node_size=700,
                    alpha=0.9,
                )
                labels = {}
                for node in subgraph:
                    resource_obj = R.RESOURCES.get(node)
                    labels[node] = (resource_obj.title if resource_obj else graph.nodes[node].get("title", str(node)))[:24]
                nx.draw_networkx_labels(subgraph, pos, labels=labels, font_size=8, ax=ax)
                edge_weights = [max(0.5, subgraph[u][v].get("similarity", 0.0) * 8) for u, v in subgraph.edges()]
                nx.draw_networkx_edges(subgraph, pos, width=edge_weights, alpha=0.6, ax=ax)
                ax.axis("off")
                st.pyplot(fig)

                st.markdown("#### Top Related Works")
                for neighbor_id, score in top_neighbors:
                    neighbor_resource = R.RESOURCES.get(neighbor_id)
                    title = neighbor_resource.title if neighbor_resource else graph.nodes[neighbor_id].get("title", "Untitled")
                    type_label = neighbor_resource.type if neighbor_resource else graph.nodes[neighbor_id].get("type", "Unknown")
                    year_label = neighbor_resource.year if neighbor_resource else graph.nodes[neighbor_id].get("year", "-")

                    st.markdown(
                        f"**{title}**  \n"
                        f"Type: {type_label}  \n"
                        f"Year: {year_label}  \n"
                        f"Similarity: {score:.3f}"
                    )
                    if neighbor_resource:
                        if st.button("Open", key=f"open-similar-{neighbor_id}"):
                            st.session_state.selected_resource = neighbor_id
                            st.experimental_rerun()
                    st.divider()

    with experiments_tab:
        st.subheader("Experiments")

        experiments = resource.experiments
        if len(experiments) > 0:
            for exp in experiments:
                st.markdown(
                    f"""
                    **{exp.icon} {exp.title}**

                    *Authors:* {', '.join(exp.authors)}  
                    *Year:* {exp.year}  
                    *Type:* {exp.type}
                    """
                )
                st.divider()
        else:
            st.write("No experiments on this publication available")

    with references_tab:
        referenced_work = resource.referenced_work
        if referenced_work is not None:
            for ref in resource.referenced_work:
                st.markdown(ref)

    with qa_tab:
        st.markdown("#### Research Q&A")
        st.caption(
            "Chat with an AI researcher about this paper. The assistant is brief, cites the paper context, "
            "and suggests follow-up ideas."
        )

        st.markdown(
            """
            <style>
            .paper-chat-container {
                background: linear-gradient(135deg, rgba(15,87,178,0.15), rgba(137,196,244,0.15));
                padding: 1.25rem;
                border-radius: 1rem;
                border: 1px solid rgba(15,87,178,0.25);
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        pdf_text_key = f"paper_pdf_text_{resource_id}"
        pdf_index_key = f"paper_pdf_index_{resource_id}"
        retrieval_key = f"paper_pdf_passages_{resource_id}"

        pdf_text: Optional[str] = st.session_state.get(pdf_text_key)
        if pdf_text is None and pdf_url:
            with st.spinner("Fetching PDF text..."):
                pdf_text = paper_chat.load_pdf_text(pdf_url)
            st.session_state[pdf_text_key] = pdf_text

        pdf_index: Optional[Dict[str, Any]] = st.session_state.get(pdf_index_key)
        retrieval_results: List[Dict[str, Any]] = st.session_state.get(
            retrieval_key, []
        )

        support_placeholder = st.empty()

        def render_supporting_passages(
            passages: List[Dict[str, Any]],
            *,
            truncated: bool,
        ) -> None:
            with support_placeholder.container():
                with st.expander("Recent supporting passages", expanded=False):
                    if passages:
                        for passage in passages:
                            score = float(passage.get("score", 0.0))
                            rank = passage.get("rank", "?")
                            text = passage.get("text", "")
                            st.markdown(
                                f"**Passage {rank}** (similarity {score:.2f})\n\n{text}",
                                unsafe_allow_html=False,
                            )
                    else:
                        st.info(
                            "No supporting passages yet. Ask a question to fetch relevant snippets."
                        )
                if truncated:
                    approx_chars = paper_chat.approx_indexed_character_count()
                    st.caption(
                        "Indexed approximately the first "
                        f"{approx_chars:,} characters of the PDF for retrieval to keep queries responsive."
                    )

        render_supporting_passages(
            retrieval_results,
            truncated=bool(pdf_index and pdf_index.get("truncated")),
        )

        chat_state_key = f"paper_chat_history_{resource_id}"
        intro_message = {
            "role": "assistant",
            "content": (
                "Hi! I'm ready to discuss this paper. I'm grounded in its title, abstract, and can pull in PDF passages when needed."
            ),
        }
        chat_history: List[Dict[str, str]] = st.session_state.setdefault(
            chat_state_key, [intro_message]
        )

        chat_placeholder = st.empty()

        def _format_message(entry: Dict[str, str]) -> str:
            role = entry.get("role", "assistant")
            content = entry.get("content", "")
            safe_content = html.escape(content).replace("\n", "<br>")
            role_class = "paper-chat-user" if role == "user" else "paper-chat-assistant"
            icon = "🤔" if role == "user" else "🔭"
            return (
                f'<div class="paper-chat-message {role_class}">'
                f'<div class="paper-chat-avatar">{icon}</div>'
                f'<div class="paper-chat-bubble">{safe_content}</div>'
                "</div>"
            )

        def render_history(
            messages: List[Dict[str, str]],
            *,
            stream_generator=None,
        ) -> Optional[str]:
            style_block = """
            <style>
            .paper-chat-scroll {
                height: 520px;
                max-height: 520px;
                overflow-y: auto;
                padding: 0.25rem 0.5rem 0.75rem;
                border-radius: 0.75rem;
                border: 1px solid rgba(15, 87, 178, 0.15);
                background: rgba(248, 250, 255, 0.6);
                display: flex;
                flex-direction: column;
                gap: 0.75rem;
                box-sizing: border-box;
            }
            .paper-chat-message {
                display: flex;
                gap: 0.75rem;
                align-items: flex-start;
                flex-shrink: 0;
            }
            .paper-chat-message.paper-chat-user {
                flex-direction: row-reverse;
            }
            .paper-chat-avatar {
                width: 32px;
                height: 32px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                background: rgba(15, 87, 178, 0.15);
                font-size: 0.9rem;
            }
            .paper-chat-user .paper-chat-avatar {
                background: rgba(52, 199, 89, 0.2);
            }
            .paper-chat-bubble {
                padding: 0.75rem 1rem;
                border-radius: 0.9rem;
                background: #ffffff;
                border: 1px solid rgba(15, 87, 178, 0.12);
                box-shadow: 0 4px 10px rgba(15, 87, 178, 0.05);
                max-width: 100%;
                word-break: break-word;
            }
            .paper-chat-user .paper-chat-bubble {
                background: rgba(52, 199, 89, 0.12);
                border-color: rgba(52, 199, 89, 0.25);
            }
            </style>
            """

            def compose(active_text: Optional[str] = None) -> str:
                body = "".join(_format_message(entry) for entry in messages)
                if active_text:
                    body += _format_message(
                        {"role": "assistant", "content": active_text}
                    )
                return style_block + f"<div class='paper-chat-scroll'>{body}</div>"

            chat_placeholder.markdown(compose(), unsafe_allow_html=True)

            if stream_generator is None:
                return None

            response_text = ""
            for chunk in stream_generator or []:
                if not chunk:
                    continue
                response_text += chunk
                chat_placeholder.markdown(
                    compose(response_text),
                    unsafe_allow_html=True,
                )

            return response_text or None

        render_history(chat_history)

        base_messages: List[Dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "You are an insightful research assistant helping a user understand a scientific paper. "
                    "Rely only on the supplied metadata, abstract, and extracted PDF passages to craft grounded answers, "
                    "and propose relevant follow-up directions when they are useful."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Paper title: {title or 'Untitled'}\n"
                    f"Primary link: {paper_url[1] if paper_url else 'Not provided'}\n"
                    f"Abstract: {paper_chat.truncate_for_context(abstract)}"
                ),
            },
        ]

        user_prompt = st.chat_input("Ask a question about this paper...")

        if user_prompt:
            user_message = {"role": "user", "content": user_prompt}
            chat_history.append(user_message)

            context_messages = list(base_messages)

            retrieval_passages: List[Dict[str, Any]] = []
            client = paper_chat.get_openai_client()
            if client:
                pdf_index_local = pdf_index
                if pdf_index_local is None and pdf_text and pdf_url:
                    with st.spinner("Indexing PDF for semantic search..."):
                        pdf_index_local = paper_chat.build_pdf_index(pdf_text, client)
                    st.session_state[pdf_index_key] = pdf_index_local
                    pdf_index = pdf_index_local

                if pdf_index_local:
                    retrieval_passages = paper_chat.retrieve_passages(
                        user_prompt, pdf_index_local, client
                    )

            st.session_state[retrieval_key] = retrieval_passages
            render_supporting_passages(
                retrieval_passages,
                truncated=bool(pdf_index and pdf_index.get("truncated")),
            )

            if retrieval_passages:
                formatted = "\n\n".join(
                    [
                        f"Passage {item['rank']} (similarity {item['score']:.2f}): {item['text']}"
                        for item in retrieval_passages
                    ]
                )
                context_messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Relevant passages from the paper to ground your answer:\n"
                            f"{formatted}"
                        ),
                    }
                )
            elif pdf_text:
                context_messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Extracted PDF text (trimmed): "
                            f"{paper_chat.truncate_for_context(pdf_text, limit=8000)}"
                        ),
                    }
                )

            messages_payload = context_messages + chat_history

            response_text = render_history(
                chat_history,
                stream_generator=paper_chat.stream_chat_response(messages_payload),
            )

            if response_text:
                chat_history.append({"role": "assistant", "content": response_text})
                render_history(chat_history)
