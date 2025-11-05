import streamlit as st
from common import *

def student_login_interface():
    st.title("🎓 Diák Quiz - Bejelentkezés")
    
    if 'student_logged_in' in st.session_state and st.session_state.student_logged_in:
        student_quiz_interface()
        return
    
    st.subheader("Bejelentkezés")
    
    login_tab, register_tab = st.tabs(["Bejelentkezés", "Regisztráció"])
    
    with login_tab:
        email = st.text_input("Email cím", key="login_email")
        password = st.text_input("Jelszó", type="password", key="login_password")
        
        if st.button("Bejelentkezés", key="login_button"):
            if email and password:
                student_info = authenticate_student(email, password)
                if student_info:
                    st.session_state.student_logged_in = True
                    st.session_state.student_name = student_info["name"]
                    st.session_state.student_class = student_info["class"]
                    st.session_state.student_email = student_info["email"]
                    st.success(f"Sikeres bejelentkezés! Üdvözöljük, {student_info['name']}!")
                    st.rerun()
                else:
                    st.error("Hibás email cím vagy jelszó!")
            else:
                st.warning("Kérjük, add meg az email címed és a jelszavad!")
    
    with register_tab:
        st.info("Ha még nincs fiókod, kérjük vedd fel a kapcsolatot a tanároddal!!")

def student_quiz_interface():
    st.title("🎓 Diák Quiz")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.write(f"**Név:** {st.session_state.student_name}")
    with col2:
        st.write(f"**Osztály:** {st.session_state.student_class}")
    with col3:
        if st.button("Kijelentkezés"):
            for key in ['student_logged_in', 'student_name', 'student_class', 'student_email',
                       'current_question', 'score', 'student_answers', 'quiz_started', 
                       'randomized_quiz', 'quiz_id', 'current_quiz_id', 'quiz_completed']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Diákoknak csak a látható quizeket jelenítjük meg
    available_quizzes = get_available_quizzes(for_student=True)
    if not available_quizzes:
        st.info("📝 Jelenleg nincsenek elérhető quizek számodra. Kérdezd meg a tanárod, hogy mikor tesz elérhetővé új quizt!")
        return
    
    config = load_config()
    active_quiz_id = config.get("active_quiz", list(available_quizzes.keys())[0])
    
    quiz_options = {qid: f"{data['name']} ({data['question_count']} kérdés)" 
                   for qid, data in available_quizzes.items()}
    
    selected_quiz_id = st.selectbox(
        "Válassz quizzet:",
        options=list(quiz_options.keys()),
        format_func=lambda x: quiz_options[x],
        key="student_quiz_selector"
    )
    
    quiz_data = load_quiz(selected_quiz_id)
    if not quiz_data:
        st.error("A kiválasztott quiz nem található.")
        return
    
    quiz_settings = config.get("quiz_settings", {}).get(selected_quiz_id, {})
    show_correct_answers = quiz_settings.get("show_correct_answers", True)
    allow_retake = quiz_settings.get("allow_retake", True)
    shuffle_questions = quiz_settings.get("shuffle_questions", True)
    
    questions_to_show = quiz_settings.get("questions_to_show", 0)
    total_questions = len(quiz_data)
    
    if questions_to_show > 0 and questions_to_show < total_questions:
        st.info(f"📊 Ebből a quizből {questions_to_show} véletlenszerűen kiválasztott kérdést kapsz meg (összesen {total_questions} kérdésből).")
    else:
        st.info(f"📊 Ez a quiz {total_questions} kérdést tartalmaz.")
    
    start_quiz = st.button("🚀 Quiz indítása", type="primary")
    
    if start_quiz:
        st.session_state.current_question = 0
        st.session_state.score = 0
        st.session_state.student_answers = []
        st.session_state.quiz_started = True
        st.session_state.current_quiz_id = selected_quiz_id
        
        if questions_to_show > 0 and questions_to_show < total_questions:
            st.session_state.randomized_quiz = get_random_subset_quiz(quiz_data, questions_to_show)
        elif shuffle_questions:
            st.session_state.randomized_quiz = get_randomized_quiz(quiz_data)
        else:
            st.session_state.randomized_quiz = quiz_data.copy()
        
        st.session_state.quiz_id = random.randint(1000, 9999)
        st.session_state.quiz_completed = False
        st.rerun()
    
    if 'quiz_started' not in st.session_state or not st.session_state.get('quiz_started'):
        return
    
    if st.session_state.get('current_quiz_id') != selected_quiz_id:
        for key in ['current_question', 'score', 'student_answers', 'quiz_started', 
                   'randomized_quiz', 'quiz_id', 'current_quiz_id', 'quiz_completed']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    def save_result():
        total_max_points = sum(q["points"] for q in st.session_state.randomized_quiz)
        percentage = round((st.session_state.score / total_max_points) * 100, 2)
        grade = calculate_grade(percentage)
        
        result = {
            "student_name": st.session_state.student_name,
            "student_email": st.session_state.student_email,
            "score": st.session_state.score,
            "total_questions": len(st.session_state.randomized_quiz),
            "percentage": percentage,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "answers": json.dumps(st.session_state.student_answers),
            "class": st.session_state.student_class,
            "max_points": total_max_points,
            "grade": grade,
            "quiz_id": st.session_state.quiz_id
        }
        
        df = load_results(selected_quiz_id)
        df = pd.concat([df, pd.DataFrame([result])], ignore_index=True)
        save_results(selected_quiz_id, df)
    
    def show_question():
        q = st.session_state.randomized_quiz[st.session_state.current_question]
        
        st.markdown(
            f"""
            <div style="background-color: #f0f8ff; padding: 20px; border-radius: 10px; border-left: 5px solid #4CAF50; margin-bottom: 20px;">
                <p style="font-size: 16px; color: #666; margin-bottom: 5px;">Kérdés {st.session_state.current_question + 1}/{len(st.session_state.randomized_quiz)}</p>
                <h2 style="color: #333; margin-bottom: 15px; font-size: 22px;">{q['question']}</h2>
                <p style="font-size: 14px; color: #777;">(Pontérték: {q['points']}) - {type_labels[q['type']]}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        if "image" in q and q["image"]:
            st.write("")
            display_image(q["image"], width=400)
            st.write("")
        
        user_answer = None
        
        if q["type"] == "single":
            user_answer = st.radio(
                "Válassz egy választ:",
                q["options"],
                key=f"single_{st.session_state.quiz_id}_{st.session_state.current_question}"
            )
        elif q["type"] == "multiple":
            st.write("**Válassz ki több választ is:**")
            user_answer = []
            for i, option in enumerate(q["options"]):
                if st.checkbox(option, key=f"multiple_{st.session_state.quiz_id}_{st.session_state.current_question}_{i}"):
                    user_answer.append(option)
        else:
            if "match_type" in q and q["match_type"] == "number":
                st.write("**Add meg a választ szám formátumban (lehet tört is, pl. 29/5):**")
                user_answer = st.text_input("Válasz:", key=f"text_{st.session_state.quiz_id}_{st.session_state.current_question}")
            else:
                st.write("**Add meg a választ szöveges formában:**")
                user_answer = st.text_area("Válasz:", height=100, key=f"text_{st.session_state.quiz_id}_{st.session_state.current_question}")
        
        if st.button("Következő"):
            if q["type"] == "multiple" and len(user_answer) == 0:
                st.warning("Kérjük, válassz ki legalább egy választ!")
                return
            if q["type"] == "text" and (user_answer is None or user_answer.strip() == ""):
                st.warning("Kérjük, add meg a választ!")
                return
            
            match_type = q.get("match_type", "exact")
            earned_points = calculate_score(user_answer, q["answer"], q["type"], q["points"], match_type)
            
            answer_data = {
                "question": q["question"],
                "type": q["type"],
                "student_answer": user_answer,
                "correct_answer": q["answer"],
                "earned_points": earned_points,
                "max_points": q["points"],
                "is_correct": earned_points == q["points"]
            }
            
            if "image" in q:
                answer_data["image"] = q["image"]
            
            if q["type"] == "text":
                answer_data["match_type"] = match_type
                answer_data["normalized_student"] = normalize_text(user_answer)
                answer_data["normalized_correct"] = [normalize_text(ca) for ca in q["answer"]]
            
            st.session_state.student_answers.append(answer_data)
            
            st.session_state.score += earned_points
            
            if st.session_state.current_question < len(st.session_state.randomized_quiz) - 1:
                st.session_state.current_question += 1
                st.rerun()
            else:
                save_result()
                st.session_state.quiz_completed = True
                st.rerun()
    
    if 'quiz_completed' in st.session_state and st.session_state.quiz_completed:
        st.balloons()
        total_max_points = sum(q["points"] for q in st.session_state.randomized_quiz)
        percentage = (st.session_state.score / total_max_points) * 100
        grade = calculate_grade(percentage)
        
        st.success(f"🎉 Quiz vége!")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Elért pontszám", f"{st.session_state.score}/{total_max_points}")
        with col2:
            st.metric("Sikereség", f"{percentage:.1f}%")
        with col3:
            grade_colors = {1: "red", 2: "orange", 3: "yellow", 4: "lightgreen", 5: "green"}
            st.markdown(f"<h2 style='color: {grade_colors[grade]};'>Osztályzat: {grade}</h2>", unsafe_allow_html=True)
        
        grade_descriptions = {
            1: "Elégtelen - További tanulásra van szükség.",
            2: "Elégséges - Alap tudás, de fejlődés szükséges.",
            3: "Közepes - Átlagos teljesítmény.",
            4: "Jó - Szilárd tudás.",
            5: "Jeles - Kiváló teljesítmény!"
        }
        st.info(f"**Értékelés:** {grade_descriptions[grade]}")
        
        if questions_to_show > 0 and questions_to_show < total_questions:
            st.info(f"ℹ️ Ebből a quizből {len(st.session_state.randomized_quiz)} véletlenszerűen kiválasztott kérdést kaptál meg (összesen {total_questions} kérdésből).")
        
        with st.expander("Részletes eredmények megtekintése"):
            for i, answer in enumerate(st.session_state.student_answers, 1):
                col1, col2 = st.columns([3, 1])
                with col1:
                    status = "✅" if answer["is_correct"] else "⚠️" if answer["earned_points"] > 0 else "❌"
                    type_label = type_labels[answer["type"]]
                    st.write(f"{status} **{i}. {answer['question']}** (*{type_label}*)")
                    
                    if "image" in answer and answer["image"]:
                        display_image(answer["image"], width=300)
                    
                    if answer["type"] == "text":
                        st.write(f"   **Te:** {answer['student_answer']}")
                        if not answer["is_correct"] and show_correct_answers:
                            st.write(f"   **Helyes válasz(ok):** {', '.join(answer['correct_answer']) if isinstance(answer['correct_answer'], list) else answer['correct_answer']}")
                            if "match_type" in answer:
                                st.write(f"   **Értékelés típusa:** {answer['match_type']}")
                        elif not answer["is_correct"] and not show_correct_answers:
                            st.write("   **Helyes válasz:** *A tanár nem engedélyezte a megjelenítést*")
                    else:
                        st.write(f"   **Te:** {', '.join(answer['student_answer']) if isinstance(answer['student_answer'], list) else answer['student_answer']}")
                        if not answer["is_correct"] and show_correct_answers:
                            correct_answer = answer['correct_answer']
                            if isinstance(correct_answer, list):
                                correct_display = ', '.join(correct_answer)
                            else:
                                correct_display = correct_answer
                            st.write(f"   **Helyes:** {correct_display}")
                        elif not answer["is_correct"] and not show_correct_answers:
                            st.write("   **Helyes válasz:** *A tanár nem engedélyezte a megjelenítést*")
                with col2:
                    st.write(f"**{answer['earned_points']}/{answer['max_points']} pont**")
        
        if not show_correct_answers:
            st.info("ℹ️ A helyes válaszok megjelenítése jelenleg ki van kapcsolva a tanári beállítások miatt.")
        
        if allow_retake:
            if st.button("Újra kezdés"):
                for key in ['current_question', 'score', 'student_answers', 'quiz_completed', 'randomized_quiz', 'quiz_id', 'current_quiz_id', 'quiz_started']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        else:
            st.warning("ℹ️ Újrakezdés jelenleg nem engedélyezett a tanári beállítások miatt.")
    else:
        show_question()

def main():
    setup_page_config()
    student_login_interface()

if __name__ == "__main__":
    main()
