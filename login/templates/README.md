# Career Assessment System

A comprehensive, self-contained career aptitude test that helps users discover their ideal career paths through personalized assessment and interactive visualizations.

## 🚀 Quick Start

### Option 1: Double-Click Launch (Recommended)
```
Double-click: start_assessment.bat
```

### Option 2: Python Launch
```bash
python start_server.py
```

### Option 3: Manual Launch
```bash
python -m http.server 8080
```
Then open: `http://localhost:8080/career_assessment.html`

## 📋 Features

### Assessment System
- **40 Questions** across 8 career domains
- **20 Random Questions** selected per assessment
- **Balanced Distribution** ensures fair domain representation
- **Non-Repetitive Experience** with question randomization

### Career Domains
1. **Engineering & Technology** - Software, AI/ML, Robotics
2. **Medical & Healthcare** - Medicine, Research, Patient Care
3. **Business & Management** - Leadership, Entrepreneurship, Analytics
4. **Arts & Creative** - Design, Media, Storytelling
5. **Science & Research** - Environmental, Physics, Chemistry
6. **Education & Social Service** - Teaching, Counseling, Social Impact
7. **Law & Government** - Legal Systems, Policy, Justice
8. **Finance & Economics** - Investment, Analysis, Planning

### Interactive Results
- **Domain Interest Scores** with visual charts
- **Top 3 Career Recommendations** with detailed information
- **Interactive Career Journey Maps** using D3.js
- **Clickable Pathway Nodes** with exam and course details
- **Tabbed Interface** to explore multiple career paths

## 🎯 Assessment Process

1. **Take Assessment** (5-10 minutes)
   - Answer 20 questions using 1-5 Likert scale
   - Questions cover interests, skills, and preferences
   - Progress tracking with visual feedback

2. **View Results**
   - Interest scores across all domains
   - Personalized career recommendations
   - Interactive career journey visualization

3. **Explore Career Paths**
   - Click on journey nodes for detailed information
   - View required exams (JEE, NEET, CAT, etc.)
   - See higher education pathways
   - Understand career progression steps

## 📁 File Structure

```
├── career_assessment.html    # Main assessment application
├── start_server.py          # Python server launcher
├── start_assessment.bat     # Windows batch launcher
└── README.md               # This file
```

## 🔧 Technical Details

### Requirements
- Python 3.x (for server)
- Modern web browser
- No external dependencies or internet required

### Technology Stack
- **Frontend**: HTML5, CSS3, JavaScript
- **Visualization**: D3.js
- **Styling**: Tailwind CSS
- **Server**: Python HTTP Server

### Browser Compatibility
- Chrome/Chromium (recommended)
- Firefox
- Safari
- Edge

## 🎨 Features Highlights

### Smart Question Selection
- Ensures balanced representation across all career domains
- Randomizes question order for fresh experience
- Prevents assessment fatigue with optimal question count

### Interactive Visualizations
- Animated career journey diagrams
- Hover tooltips with detailed information
- Clickable nodes for exam and course details
- Responsive design for all screen sizes

### Comprehensive Career Data
- Specific job roles and career options
- Relevant competitive exams for each domain
- Higher education pathways and requirements
- Step-by-step career progression roadmaps

## 🔄 Retaking the Assessment

The system supports multiple assessments with:
- Different question combinations each time
- Fresh randomization for varied experience
- Consistent accuracy across attempts
- No data persistence (privacy-focused)

## 🛠️ Troubleshooting

### Server Won't Start
- Ensure Python is installed and in PATH
- Check if port 8080 is available
- Try running as administrator

### Browser Issues
- Clear browser cache and cookies
- Try a different browser
- Disable browser extensions temporarily

### Assessment Not Loading
- Verify `career_assessment.html` exists in directory
- Check browser console for JavaScript errors
- Ensure server is running on correct port

## 📞 Support

For technical issues or questions:
1. Check browser console for error messages
2. Verify all files are in the same directory
3. Ensure Python is properly installed
4. Try restarting the server

---

**Built with ❤️ for career guidance and educational purposes**
