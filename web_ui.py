#!/usr/bin/env python3
"""
Web UI for SMTP Relay - communicates with the API server
"""
from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)
app.secret_key = 'smtp_relay_secret_key'  # Change this in production

# Configuration - API server location
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:5001')

@app.route('/')
def index():
    return render_template('index.html')

# Proxy all API calls to the API server
@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_api(path):
    """Proxy API requests to the backend API server"""
    # Build the target URL
    target_url = f"{API_BASE_URL}/api/{path}"
    
    # Determine the HTTP method from the original request
    method = request.method
    headers = {key: value for (key, value) in request.headers if key != 'Host'}
    data = request.get_json() if request.is_json else request.data
    
    try:
        # Forward the request to the API server
        if method == 'GET':
            response = requests.get(target_url, headers=headers)
        elif method == 'POST':
            response = requests.post(target_url, json=data, headers=headers)
        elif method == 'PUT':
            response = requests.put(target_url, json=data, headers=headers)
        elif method == 'DELETE':
            response = requests.delete(target_url, headers=headers)
        else:
            return jsonify({"error": "Method not allowed"}), 405
            
        # Return the response from the API server
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to connect to API server: {str(e)}"}), 502
    except ValueError:
        # Handle case where response is not JSON
        return {"error": "Invalid response from API server"}, 502

if __name__ == '__main__':
    # Create a simple HTML template if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Create an updated index.html template that communicates with API server
    template_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SMTP Relay - Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
    <style>
        :root {
            --primary-color: #4361ee;
            --secondary-color: #3f37c9;
            --success-color: #4cc9f0;
            --danger-color: #f72585;
            --warning-color: #f8961e;
            --light-bg: #f8f9fa;
            --dark-text: #212529;
        }
        
        body {
            background-color: #f5f7fb;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: var(--dark-text);
            padding-top: 20px;
            padding-bottom: 40px;
        }
        
        .dashboard-header {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 25px 0;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        
        .dashboard-header h1 {
            font-weight: 600;
            margin-bottom: 0;
        }
        
        .dashboard-header p {
            opacity: 0.9;
            margin-bottom: 0;
        }
        
        .card {
            border-radius: 12px;
            border: none;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            margin-bottom: 25px;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }
        
        .card-header {
            background-color: white;
            border-bottom: 1px solid rgba(0,0,0,0.05);
            padding: 18px 20px;
            border-radius: 12px 12px 0 0 !important;
            font-weight: 600;
            color: var(--primary-color);
        }
        
        .stat-card {
            text-align: center;
            padding: 20px;
        }
        
        .stat-card .icon {
            font-size: 2.5rem;
            margin-bottom: 15px;
        }
        
        .stat-card .number {
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary-color);
            margin: 10px 0;
        }
        
        .form-group {
            margin-bottom: 1.2rem;
        }
        
        .form-label {
            font-weight: 500;
            color: #495057;
        }
        
        .btn-primary {
            background-color: var(--primary-color);
            border-color: var(--primary-color);
            padding: 10px 20px;
        }
        
        .btn-primary:hover {
            background-color: var(--secondary-color);
            border-color: var(--secondary-color);
        }
        
        .btn-danger {
            background-color: var(--danger-color);
            border-color: var(--danger-color);
        }
        
        .btn-warning {
            background-color: var(--warning-color);
            border-color: var(--warning-color);
        }
        
        .status.success {
            background-color: #d1fae5;
            color: #065f46;
            padding: 12px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #10b981;
        }
        
        .status.error {
            background-color: #fee2e2;
            color: #b91c1c;
            padding: 12px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #ef4444;
        }
        
        .status.info {
            background-color: #dbeafe;
            color: #1e40af;
            padding: 12px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #3b82f6;
        }
        
        .queue-content {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            max-height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
        }
        
        .action-buttons .btn {
            margin-right: 8px;
            margin-bottom: 8px;
        }
        
        footer {
            text-align: center;
            margin-top: 40px;
            color: #6c757d;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="dashboard-header text-center">
            <div class="container">
                <h1><i class="bi bi-envelope-check"></i> SMTP Relay Dashboard</h1>
                <p class="lead">Manage your email relay configurations with ease</p>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-3">
                <div class="card stat-card">
                    <div class="icon text-primary">
                        <i class="bi bi-people"></i>
                    </div>
                    <div class="number" id="senders-count">0</div>
                    <div>Senders</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card">
                    <div class="icon text-success">
                        <i class="bi bi-check-circle"></i>
                    </div>
                    <div class="number" id="status-postfix">?</div>
                    <div>Postfix Status</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card">
                    <div class="icon text-warning">
                        <i class="bi bi-envelope"></i>
                    </div>
                    <div class="number" id="queue-count">0</div>
                    <div>In Queue</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card">
                    <div class="icon text-info">
                        <i class="bi bi-gear"></i>
                    </div>
                    <div class="number">10+</div>
                    <div>Features</div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-lg-6">
                <div class="card">
                    <div class="card-header">
                        <i class="bi bi-send"></i> Send Test Email
                    </div>
                    <div class="card-body">
                        <form id="test-email-form">
                            <div class="form-group">
                                <label for="from_email" class="form-label">From Email</label>
                                <select class="form-select" id="from_email" required>
                                    <option value="">Select sender</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="to_email" class="form-label">To Email</label>
                                <input type="email" class="form-control" id="to_email" placeholder="recipient@example.com" required>
                            </div>
                            <div class="form-group">
                                <label for="subject" class="form-label">Subject</label>
                                <input type="text" class="form-control" id="subject" placeholder="Email subject" required>
                            </div>
                            <div class="form-group">
                                <label for="body" class="form-label">Message</label>
                                <textarea class="form-control" id="body" rows="4" placeholder="Your message here..." required></textarea>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">
                                <i class="bi bi-send-fill"></i> Send Test Email
                            </button>
                        </form>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <i class="bi bi-person-plus"></i> Add New Sender
                    </div>
                    <div class="card-body">
                        <form id="add-sender-form">
                            <div class="form-group">
                                <label for="sender_name" class="form-label">Name</label>
                                <input type="text" class="form-control" id="sender_name" placeholder="Sender display name" required>
                            </div>
                            <div class="form-group">
                                <label for="sender_email" class="form-label">Email</label>
                                <input type="email" class="form-control" id="sender_email" placeholder="sender@example.com" required>
                            </div>
                            <div class="form-group">
                                <label for="relay_host" class="form-label">Relay Host</label>
                                <input type="text" class="form-control" id="relay_host" placeholder="e.g., smtp-relay.brevo.com:587">
                            </div>
                            <div class="form-group">
                                <label for="username" class="form-label">Username</label>
                                <input type="text" class="form-control" id="username" placeholder="SMTP username">
                            </div>
                            <div class="form-group">
                                <label for="password" class="form-label">Password</label>
                                <input type="password" class="form-control" id="password" placeholder="SMTP password">
                            </div>
                            <button type="submit" class="btn btn-primary w-100">
                                <i class="bi bi-person-plus"></i> Add Sender
                            </button>
                        </form>
                    </div>
                </div>
            </div>
            
            <div class="col-lg-6">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <span><i class="bi bi-people"></i> Senders</span>
                        <span class="badge bg-primary" id="senders-badge">0</span>
                    </div>
                    <div class="card-body">
                        <div id="senders-list">
                            <div class="text-center py-4">
                                <i class="bi bi-people fs-1 text-muted"></i>
                                <p class="text-muted">No senders configured yet</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <i class="bi bi-inboxes"></i> Mail Queue
                    </div>
                    <div class="card-body">
                        <div class="queue-content" id="queue-info">Loading...</div>
                        <div class="mt-3 text-end">
                            <button id="flush-queue-btn" class="btn btn-warning">
                                <i class="bi bi-x-circle"></i> Flush Queue
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="message"></div>
        
        <footer class="mt-5">
            <p>SMTP Relay Setup Tool &copy; 2025 | Secure Email Relay Configuration</p>
        </footer>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Base API URL - can be configured via environment or settings
        const API_BASE_URL = window.location.origin + '/api';
        
        // Load status on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadStatus();
            loadSenders();
            loadQueue();
        });

        function loadStatus() {
            fetch(API_BASE_URL + '/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('senders-count').textContent = data.senders_count;
                    document.getElementById('senders-badge').textContent = data.senders_count;
                    if (data.postfix_running) {
                        document.getElementById('status-postfix').innerHTML = '<i class=\"bi bi-check-circle-fill text-success\"></i>';
                    } else {
                        document.getElementById('status-postfix').innerHTML = '<i class=\"bi bi-x-circle-fill text-danger\"></i>';
                        console.warn('Postfix is not running properly - some functions may be limited');
                    }
                    
                    // Get queue count
                    fetch(API_BASE_URL + '/mail_queue')
                        .then(response => response.json())
                        .then(queueData => {
                            if (queueData.status === 'success') {
                                // Simple count of non-empty lines as a proxy for queue items
                                const lines = queueData.queue.split('\\n');
                                let count = 0;
                                for (let line of lines) {
                                    if (line.trim() !== '' && !line.includes('Mail queue is empty') && !line.includes('-Queue ID-')) {
                                        count++;
                                    }
                                }
                                document.getElementById('queue-count').textContent = count > 0 ? count : '0';
                            } else {
                                document.getElementById('queue-count').textContent = '?';
                                console.warn('Queue status:', queueData.message || 'Unknown error');
                            }
                        })
                        .catch(error => {
                            document.getElementById('queue-count').textContent = '?';
                            console.error('Error getting queue count:', error);
                        });
                })
                .catch(error => {
                    document.getElementById('status-postfix').innerHTML = '<i class=\"bi bi-x-circle-fill text-danger\"></i>';
                    console.error('Error:', error);
                    showMessage('Error loading status: ' + error, 'error');
                });
        }

        function loadSenders() {
            fetch(API_BASE_URL + '/senders')
                .then(response => response.json())
                .then(data => {
                    const select = document.getElementById('from_email');
                    select.innerHTML = '<option value=\"\">Select sender</option>';
                    
                    data.forEach((sender, index) => {
                        const option = document.createElement('option');
                        option.value = sender.email;
                        option.textContent = sender.name + ' <' + sender.email + '>';
                        select.appendChild(option);
                    });

                    // Also update senders list display
                    const sendersList = document.getElementById('senders-list');
                    if (data.length === 0) {
                        sendersList.innerHTML = '<div class=\"text-center py-4\">' +
                            '<i class=\"bi bi-people fs-1 text-muted\"></i>' +
                            '<p class=\"text-muted\">No senders configured yet</p>' +
                            '</div>';
                    } else {
                        let html = '<div class=\"table-responsive\"><table class=\"table table-hover\">';
                        html += '<thead><tr><th>Name</th><th>Email</th><th>Relay</th><th>Actions</th></tr></thead><tbody>';
                        data.forEach((sender, index) => {
                            const relay = sender.relay_host || 'Not configured';
                            const badgeClass = relay !== 'Not configured' ? 'success' : 'secondary';
                            html += '<tr>' +
                                '<td>' + sender.name + '</td>' +
                                '<td>' + sender.email + '</td>' +
                                '<td><span class=\"badge bg-' + badgeClass + '\">' + relay + '</span></td>' +
                                '<td>' +
                                    '<button class=\"btn btn-sm btn-danger\" onclick=\"deleteSender(' + index + ')\">' +
                                        '<i class=\"bi bi-trash\"></i> Delete' +
                                    '</button>' +
                                '</td>' +
                            '</tr>';
                        });
                        html += '</tbody></table></div>';
                        sendersList.innerHTML = html;
                    }
                    
                    // Update the senders count in the header
                    document.getElementById('senders-count').textContent = data.length;
                    document.getElementById('senders-badge').textContent = data.length;
                })
                .catch(error => {
                    console.error('Error:', error);
                    showMessage('Error loading senders: ' + error, 'error');
                });
        }

        function loadQueue() {
            fetch(API_BASE_URL + '/mail_queue')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        document.getElementById('queue-info').textContent = data.queue;
                    } else {
                        document.getElementById('queue-info').textContent = 'Error loading queue: ' + (data.message || 'Unknown error');
                        console.warn('Queue error:', data.message);
                    }
                })
                .catch(error => {
                    document.getElementById('queue-info').textContent = 'Error loading queue: ' + error;
                    console.error('Queue fetch error:', error);
                    showMessage('Error loading queue: ' + error, 'error');
                });
        }

        document.getElementById('test-email-form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const fromSelect = document.getElementById('from_email');
            const selectedOption = fromSelect.options[fromSelect.selectedIndex];
            
            const data = {
                from_email: document.getElementById('from_email').value,
                from_name: selectedOption.text.split('<')[0].trim(),
                to_email: document.getElementById('to_email').value,
                subject: document.getElementById('subject').value,
                body: document.getElementById('body').value
            };
            
            fetch(API_BASE_URL + '/send_test_email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                showMessage(data.message, data.status === 'success' ? 'success' : 'error');
                if (data.status === 'success') {
                    document.getElementById('test-email-form').reset();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showMessage('Error sending email: ' + error, 'error');
            });
        });

        document.getElementById('add-sender-form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const data = {
                name: document.getElementById('sender_name').value,
                email: document.getElementById('sender_email').value,
                relay_host: document.getElementById('relay_host').value,
                username: document.getElementById('username').value,
                password: document.getElementById('password').value
            };
            
            fetch(API_BASE_URL + '/senders', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                showMessage(data.status === 'success' ? 'Sender added successfully!' : 'Error adding sender: ' + data.message, 
                           data.status === 'success' ? 'success' : 'error');
                if (data.status === 'success') {
                    document.getElementById('add-sender-form').reset();
                    loadSenders();
                    loadStatus();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showMessage('Error adding sender: ' + error, 'error');
            });
        });

        document.getElementById('flush-queue-btn').addEventListener('click', function() {
            if (confirm('Are you sure you want to flush the entire mail queue? This will attempt to deliver all queued messages.')) {
                fetch(API_BASE_URL + '/flush_queue', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showMessage(data.message, 'info');
                    } else {
                        showMessage(data.message || 'Error flushing queue', 'error');
                    }
                    loadQueue();
                    loadStatus(); // Refresh status after flush
                })
                .catch(error => {
                    console.error('Error:', error);
                    showMessage('Error flushing queue: ' + error, 'error');
                });
            }
        });

        function deleteSender(index) {
            if (confirm('Are you sure you want to delete this sender? This action cannot be undone.')) {
                fetch(API_BASE_URL + '/senders/' + index, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                })
                .then(response => response.json())
                .then(data => {
                    showMessage(data.status === 'success' ? 'Sender deleted successfully!' : 'Error deleting sender: ' + data.message, 
                               data.status === 'success' ? 'success' : 'error');
                    if (data.status === 'success') {
                        loadSenders();
                        loadStatus();
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showMessage('Error deleting sender: ' + error, 'error');
                });
            }
        }

        function showMessage(message, type) {
            const messageDiv = document.getElementById('message');
            
            // Map our types to Bootstrap classes
            let bsClass = '';
            switch(type) {
                case 'success':
                    bsClass = 'alert-success';
                    break;
                case 'error':
                    bsClass = 'alert-danger';
                    break;
                case 'info':
                    bsClass = 'alert-info';
                    break;
                default:
                    bsClass = 'alert-secondary';
            }
            
            messageDiv.innerHTML = '<div class=\"alert ' + bsClass + ' alert-dismissible fade show\" role=\"alert\">' +
                message +
                '<button type=\"button\" class=\"btn-close\" data-bs-dismiss=\"alert\" aria-label=\"Close\"></button>' +
            '</div>';
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                const alert = document.querySelector('.alert');
                if (alert) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, 5000);
        }
    </script>
</body>
</html>"""
    
    with open('templates/index.html', 'w') as f:
        f.write(template_content)
    
    print(f"Starting Web UI on port 5000, connecting to API server at {API_BASE_URL}")
    app.run(host='0.0.0.0', port=5000, debug=False)