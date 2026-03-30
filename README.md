# Student Collaboration Portal (CollabHub)

Welcome to the **Student Collaboration Portal**, an interactive and feature-rich platform designed to help students connect, study together, and manage their academic projects efficiently.

## 🚀 Key Features

*   **Student Dashboard**: A personalized hub to view recent posts, upcoming tasks, and community updates.
*   **Project Management**: Create projects, form teams, and manage tasks using an integrated Kanban board (To Do, In Progress, Done).
*   **Gamification & Badges**: Earn XP and unlock badges (e.g., *Team Player*, *Task Master*, *Project Lead*) by actively participating in the community.
*   **Course Rooms**: Join specific course rooms to share resources, ask questions, and interact with classmates taking the same subjects.
*   **Skill Matching**: Find the perfect teammates for your projects based on matching skills and overlapping interests.
*   **Activity Feed & Community Interactions**: Post updates, like posts, and collaborate on the community feed.
*   **Study Tools**: Keep track of your academic life with personal Sticky Notes, a To-Do list, and a unified Calendar.
*   **Resource Sharing**: Upload and request study materials directly within your project teams.

## 🛠️ Technologies Used

*   **Backend**: Python, Flask
*   **Frontend**: HTML, CSS, JavaScript, Jinja2 Templates
*   **Database**: JSON-based persistent local storage
*   **Deployment**: Vercel / Render

## 💻 Running the Project Locally

1. **Clone the repository** (or download the files):
   ```bash
   git clone https://github.com/Harjithreddy14/Student-Collaboration-Portal.git
   cd Student-Collaboration-Portal
   ```

2. **Install the required dependencies**:
   Ensure you have Python installed. Then, run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the Flask server**:
   ```bash
   python app.py
   ```
   *(Or alternatively, `flask run`)*

4. **Access the application**:
   Open your web browser and go to `http://127.0.0.1:5000`

## 🌐 Deployment (Vercel)

This application is ready to be deployed on serverless platforms like Vercel. 
*Note: Due to Vercel's read-only file system, the application has been configured to use the `/tmp` directory to handle dynamic JSON data operations temporarily.*

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! 
Feel free to check the issues page or submit a Pull Request to help improve the platform.
