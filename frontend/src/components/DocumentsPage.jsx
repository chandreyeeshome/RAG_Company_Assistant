import { useEffect, useState } from "react";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState([]);
  const [form, setForm] = useState({ title: "", content: "", category: "" });

  useEffect(() => {
    fetch(`${BASE_URL}/documents`)
      .then((res) => res.json())
      .then((data) => setDocuments(data.data))
      .catch(() => {});
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();

    await fetch(`${BASE_URL}/documents`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });

    setForm({ title: "", content: "", category: "" });

    const res = await fetch(`${BASE_URL}/documents`);
    const data = await res.json();
    setDocuments(data.data);
  };

  const handleDelete = async (id) => {
    await fetch(`${BASE_URL}/documents/${id}`, { method: "DELETE" });
    // Filter by either _id or id — handles both MongoDB and other backends
    setDocuments((prev) =>
      prev.filter((doc) => (doc._id ?? doc.id) !== id)
    );
  };

  return (
    <div className="docs-container">
      <h2 className="docs-heading">Document Management</h2>

      <form className="doc-form" onSubmit={handleSubmit}>
        <div className="doc-form-row">
          <input
            type="text"
            placeholder="Title"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
          />
          <input
            type="text"
            placeholder="Category"
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
          />
        </div>

        <textarea
          placeholder="Content"
          value={form.content}
          onChange={(e) => setForm({ ...form, content: e.target.value })}
        />

        <button type="submit">Add Document</button>
      </form>

      <div className="docs-list-section">
        <h3 className="docs-list-heading">Saved Documents</h3>

        <div className="docs-list">
          {documents.map((doc) => {
            const id = doc._id ?? doc.id;
            return (
              <div key={id} className="doc-card">
                <div className="doc-card-header">
                  <h3>{doc.title}</h3>
                  <span className="category">{doc.category}</span>
                </div>
                <p>{doc.content}</p>
                <button onClick={() => handleDelete(id)}>Delete</button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
