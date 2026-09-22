# Looker Conversational Analytics Embedding Reference

Looker Conversational Analytics allows you to embed AI-powered conversational data exploration directly into your external application. Users can ask questions in natural language and receive visualizations and answers based on defined Looker models.

---

## 1. Embed Paths

Depending on the desired user experience, you can embed either the entire Conversations Hub or a specific conversation thread.

### Conversations Hub
To embed the main interface where users can view their past conversations and start new ones, use the following path:
```
/embed/conversations
```

### Specific Conversation Thread
To load a specific conversation directly, append the conversation ID to the path:
```
/embed/conversations/<conversation_id>
```

---

## 2. Required Permissions

To enable Conversational Analytics for embedded users, their Signed SSO embed URL or Cookieless JWT session must include the following permissions:

- **`chat_with_explore`**: Allows the user to ask questions and explore data using natural language within the context of a Looker Explore.
- **`chat_with_agent`**: Enables interaction with Looker's AI agent for deeper conversational analysis and assistance.

These permissions must be provided in the permissions array when generating the embed authentication token.

---

## 3. Controlling Chat Visibility on Embedded Dashboards

By default, embedded Looker dashboards may display a conversational chat action button allowing users to launch a chat drawer directly.

If you wish to hide this chat button and control the chat experience outside the dashboard (e.g. via a dedicated tab or custom button in your host application), append the `ca_chat` parameter to the dashboard's embed URL:

```
/embed/dashboards/<dashboard_id>?ca_chat=false
```

Setting `ca_chat=false` suppresses the default Looker chat floating action button or toolbar icon on the dashboard.
