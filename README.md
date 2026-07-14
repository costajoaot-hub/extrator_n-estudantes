# extrator_n-estudantes
Script for extracting the number of students enrolled in Course Units on the FEUP's Sigarra portal for a given academic year.

The script is intelligently designed to handle complex cases where a course unit has multiple occurrences throughout the year, automatically visiting each unique page and summing up the total student count.

## ✨ Features
- **Multi-Semester/Occurrence Support:** If a UC runs in multiple semesters or has multiple instances, the scraper navigates to each specific occurrence link, extracts the counts, and calculates the cumulative sum.
- **Secure MFA (Multi-Factor Authentication) Support:** It launches an isolated, clean Chrome instance and pauses for 60 seconds at the beginning to allow you to log in securely and complete your Mobile/App MFA authentication. Once authenticated, the script resumes and handles all requests within your active session.
- **Incremental Progress Saving:** The Excel sheet is updated and saved row by row in real-time. If the process is interrupted or the network drops, you will not lose previously fetched data.
- **Clean Local Profile:** Uses a temporary Selenium-specific user data directory to prevent configuration conflicts with your personal everyday Chrome profile.

## 📋 Prerequisites
Ensure you have the following installed on your machine:
- Python 3.8 or higher
- Google Chrome browser

## 🚀 Getting Started

1. **Clone this repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/your-repo-name.git](https://github.com/YOUR_USERNAME/your-repo-name.git)
   cd your-repo-name
