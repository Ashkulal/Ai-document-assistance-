from fpdf import FPDF


class ResumePDF(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(79, 70, 229)
        self.cell(0, 10, title.upper(), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(79, 70, 229)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        x = self.get_x()
        self.cell(5, 5.5, "-")
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def skill_row(self, category, skills):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(50, 50, 50)
        self.cell(40, 6, category + ":")
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 6, skills)
        self.ln(1)


def generate_resume():
    pdf = ResumePDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Name
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 12, "AKASH H R", align="C", new_x="LMARGIN", new_y="NEXT")

    # Title
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 7, "Computer Science Student | Full-Stack Developer", align="C", new_x="LMARGIN", new_y="NEXT")

    # Contact
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, "Mangalore, Karnataka | akashhr@email.com | linkedin.com/in/akashhr | github.com/akashhr", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Objective
    pdf.section_title("Objective")
    pdf.body_text("Motivated Computer Science student with strong full-stack development skills seeking to leverage expertise in Java, Python, React, and AI/ML to contribute to innovative projects and gain professional experience.")

    # Education
    pdf.section_title("Education")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 6, "Bachelor of Engineering in Computer Science", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Mangalore, Karnataka | 2022 - 2026", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Skills
    pdf.section_title("Technical Skills")
    pdf.skill_row("Languages", "Java, Python, JavaScript, TypeScript, Dart")
    pdf.skill_row("Frontend", "React.js, Next.js, Flutter, HTML5, CSS3, Tailwind CSS")
    pdf.skill_row("Backend", "Spring Boot, Node.js, Express.js, Flask, REST APIs")
    pdf.skill_row("Database", "MySQL, PostgreSQL, MongoDB, Firebase")
    pdf.skill_row("AI/ML", "LangChain, OpenAI API, TensorFlow, scikit-learn")
    pdf.skill_row("Tools", "Git, Docker, Linux, VS Code, IntelliJ IDEA")
    pdf.ln(2)

    # Projects
    pdf.section_title("Projects")

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 6, "AI Document Assistant", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "Python, LangChain, OpenAI API, Flask, Streamlit", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)
    pdf.bullet("Built a Python-based assistant that uses LangChain and OpenAI API to answer questions over uploaded documents")
    pdf.bullet("Implemented vector embeddings with FAISS for fast document retrieval and context-aware responses")
    pdf.bullet("Developed both web UI (Streamlit/Flask) and desktop GUI (Tkinter) interfaces")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Silent Peak - Kudremukh Homestay Website", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "React, Node.js, MongoDB, Tailwind CSS", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)
    pdf.bullet("Developed a full-stack booking website for a homestay in Kudremukh, Karnataka")
    pdf.bullet("Implemented user authentication, room booking system, and admin dashboard")
    pdf.ln(2)

    # Internship
    pdf.section_title("Internship Experience")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 6, "Full-Stack Developer Intern", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Glowlogics Solutions | 2024", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.bullet("Developed and maintained web applications using React and Spring Boot")
    pdf.bullet("Collaborated with team members on agile development processes")
    pdf.bullet("Built RESTful APIs and integrated third-party services")
    pdf.ln(2)

    # Certifications
    pdf.section_title("Certifications")
    pdf.bullet("AWS Cloud Practitioner")
    pdf.bullet("Python for Data Science - Coursera")
    pdf.bullet("React - The Complete Guide - Udemy")

    pdf.output("Akash_HR_Resume.pdf")
    print("Resume generated: Akash_HR_Resume.pdf")


if __name__ == "__main__":
    generate_resume()
