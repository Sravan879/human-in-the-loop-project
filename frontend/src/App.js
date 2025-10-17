import React, { useState, useEffect } from 'react';
import './App.css';

// The URL of our FastAPI backend
const API_URL = 'http://127.0.0.1:8000';

function App() {
  const [requests, setRequests] = useState([]);
  const [knowledge, setKnowledge] = useState([]);
  const [answers, setAnswers] = useState({});

  // Function to fetch all data from the backend
  const fetchData = async () => {
    try {
      const requestsRes = await fetch(`${API_URL}/help-requests`);
      const requestsData = await requestsRes.json();
      setRequests(requestsData);

      const knowledgeRes = await fetch(`${API_URL}/knowledge-base`);
      const knowledgeData = await knowledgeRes.json();
      setKnowledge(knowledgeData);
    } catch (error) {
      console.error("Failed to fetch data:", error);
    }
  };

  // useEffect runs this function once when the component loads
  useEffect(() => {
    fetchData();
  }, []);

  const handleAnswerChange = (id, value) => {
    setAnswers({ ...answers, [id]: value });
  };

  const handleSubmit = async (requestId) => {
    const answer = answers[requestId];
    if (!answer) {
      alert("Please provide an answer.");
      return;
    }

    try {
      await fetch(`${API_URL}/help-requests/${requestId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ answer: answer }),
      });
      alert("Response submitted successfully!");
      setAnswers({ ...answers, [requestId]: '' }); // Clear input
      fetchData(); // Refresh the data
    } catch (error) {
      console.error("Failed to submit answer:", error);
      alert("Failed to submit answer.");
    }
  };

  const pendingRequests = requests.filter(r => r.status === 'pending');
  const resolvedRequests = requests.filter(r => r.status === 'resolved');

  return (
    <div className="container">
      <h1>Supervisor Dashboard</h1>
      
      <div className="section">
        <h2>Pending Requests ({pendingRequests.length})</h2>
        {pendingRequests.length === 0 ? <p>No pending requests.</p> : (
          <div className="request-list">
            {pendingRequests.map(req => (
              <div key={req.id} className="request-card pending">
                <p><strong>Customer:</strong> {req.customer_id}</p>
                <p><strong>Question:</strong> "{req.question}"</p>
                <textarea
                  placeholder="Type your answer here..."
                  value={answers[req.id] || ''}
                  onChange={(e) => handleAnswerChange(req.id, e.target.value)}
                />
                <button onClick={() => handleSubmit(req.id)}>Submit Answer</button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="section">
        <h2>Learned Answers ({knowledge.length})</h2>
        <div className="knowledge-list">
          {knowledge.map((item, index) => (
            <div key={index} className="knowledge-card">
              <p><strong>Question:</strong> {item.question}</p>
              <p><strong>Answer:</strong> {item.answer}</p>
            </div>
          ))}
        </div>
      </div>
      
      <div className="section">
        <h2>Resolved History ({resolvedRequests.length})</h2>
        <div className="request-list">
          {resolvedRequests.map(req => (
            <div key={req.id} className="request-card resolved">
              <p><strong>Question:</strong> "{req.question}"</p>
              <p><strong>Answer:</strong> {req.supervisor_answer}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;
