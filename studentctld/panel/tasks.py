"""Task deploy / scoring / leaderboard helpers."""
import random
from datetime import datetime

from models import db, User, Task, TaskAttempt
import server_api

SPEED_BONUS = {1: 50, 2: 40, 3: 30, 4: 20, 5: 10}

TASK1_TITLE = "جستجوی فایل پنهان"
TASK1_DESC = (
    "یک درخت تصادفی دایرکتوری در پوشه task1 شما ساخته شده است. "
    "فایل result.txt را پیدا کنید (سرنخ) و سپس فایلی با نام معنادار "
    "که عدد واقعی را در خود دارد پیدا کرده، عدد را در answer.txt "
    "ذخیره کنید و دستور submit را اجرا کنید."
)

TASK2_TITLE = "ساخت ساختار پوشه مدرسه"
TASK2_DESC = (
    "ساختار زیر را در پوشه خانه خود ایجاد کنید:\n"
    "school/computer/first-project\n"
    "school/computer/second-project\n"
    "school/physic\n"
    "school/math\n"
    "سپس دستور submit را اجرا کنید."
)


def _get_approved_students():
    return (
        User.query
        .filter_by(role="student", status="approved")
        .filter(User.uid.isnot(None))
        .all()
    )


def _reset_attempts(task, students):
    for s in students:
        old = TaskAttempt.query.filter_by(task_id=task.id, user_id=s.id).first()
        if old:
            db.session.delete(old)
        db.session.add(TaskAttempt(task_id=task.id, user_id=s.id))


def deploy_task1():
    students = _get_approved_students()
    if not students:
        raise ValueError("هیچ دانشجوی فعالی وجود دارد.")

    task = Task.query.filter_by(name="task1").first()
    if not task:
        task = Task(name="task1", title=TASK1_TITLE,
                    description=TASK1_DESC, max_points=100)
        db.session.add(task)
        db.session.flush()

    student_data = []
    for s in students:
        answer = random.randint(0, 11)
        old = TaskAttempt.query.filter_by(task_id=task.id, user_id=s.id).first()
        if old:
            db.session.delete(old)
        db.session.add(TaskAttempt(
            task_id=task.id, user_id=s.id, expected_answer=str(answer),
        ))
        student_data.append({
            "username": s.username, "uid": s.uid, "answer": answer,
        })

    db.session.flush()
    server_api.deploy_task1(student_data)

    task.title = TASK1_TITLE
    task.description = TASK1_DESC
    task.is_active = True
    task.deployed_at = datetime.utcnow()
    db.session.commit()
    return len(student_data)


def deploy_task2():
    students = _get_approved_students()
    if not students:
        raise ValueError("هیچ دانشجوی فعالی وجود دارد.")

    task = Task.query.filter_by(name="task2").first()
    if not task:
        task = Task(name="task2", title=TASK2_TITLE,
                    description=TASK2_DESC, max_points=100)
        db.session.add(task)
        db.session.flush()

    _reset_attempts(task, students)

    task.title = TASK2_TITLE
    task.description = TASK2_DESC
    task.is_active = True
    task.deployed_at = datetime.utcnow()
    db.session.commit()
    return len(students)


def _complete(task, attempt):
    attempt.completed = True
    attempt.completed_at = datetime.utcnow()
    if task.deployed_at:
        delta = attempt.completed_at - task.deployed_at
        attempt.time_taken_seconds = int(delta.total_seconds())
    else:
        attempt.time_taken_seconds = 0
    done = (
        TaskAttempt.query
        .filter_by(task_id=task.id, completed=True)
        .filter(TaskAttempt.id != attempt.id)
        .count()
    )
    attempt.rank = done + 1
    attempt.score = task.max_points + SPEED_BONUS.get(attempt.rank, 0)


def process_submission(username, answer, task1_exists, task2_ok):
    user = User.query.filter_by(username=username, role="student").first()
    if not user:
        return {"ok": False, "message": "کاربر یافت نشد."}, 404

    results = []
    any_correct = False

    for task in Task.query.filter_by(is_active=True).all():
        attempt = TaskAttempt.query.filter_by(
            task_id=task.id, user_id=user.id
        ).first()
        if not attempt:
            continue
        if attempt.completed:
            results.append({
                "task": task.name, "status": "done",
                "message": f"این تسک قبلاً تکمیل شده. امتیاز: {attempt.score}",
            })
            continue

        if task.name == "task1":
            if not task1_exists:
                attempt.wrong_attempts += 1
                results.append({
                    "task": "task1", "status": "wrong",
                    "message": "دایرکتوری task1 حذف شده! نباید همه چیز را پاک کنید.",
                })
            elif str(answer).strip() == str(attempt.expected_answer).strip():
                _complete(task, attempt)
                any_correct = True
                msg = f"تسک ۱ درست! امتیاز: {attempt.score}"
                if attempt.rank <= 5:
                    msg += f" (رتبه {attempt.rank} - جایزه سرعت!)"
                results.append({
                    "task": "task1", "status": "correct",
                    "score": attempt.score, "rank": attempt.rank,
                    "message": msg,
                })
            else:
                attempt.wrong_attempts += 1
                results.append({
                    "task": "task1", "status": "wrong",
                    "message": "پاسخ اشتباه. دوباره تلاش کنید.",
                })

        elif task.name == "task2":
            if task2_ok:
                _complete(task, attempt)
                any_correct = True
                msg = f"تسک ۲ درست! امتیاز: {attempt.score}"
                if attempt.rank <= 5:
                    msg += f" (رتبه {attempt.rank} - جایزه سرعت!)"
                results.append({
                    "task": "task2", "status": "correct",
                    "score": attempt.score, "rank": attempt.rank,
                    "message": msg,
                })
            else:
                attempt.wrong_attempts += 1
                results.append({
                    "task": "task2", "status": "wrong",
                    "message": "ساختار دایرکتوری هنوز کامل نیست.",
                })

    db.session.commit()
    if not results:
        return {"ok": False, "message": "تسک فعالی وجود ندارد."}, 200
    return {
        "ok": any_correct,
        "message": " | ".join(r["message"] for r in results),
        "details": results,
    }, 200


def leaderboard_data():
    students = (
        User.query
        .filter_by(role="student", status="approved")
        .filter(User.uid.isnot(None))
        .order_by(User.username)
        .all()
    )
    tasks = Task.query.order_by(Task.id).all()
    rows = []
    for s in students:
        scores = {}
        total = 0
        completed = 0
        first_time = None
        for t in tasks:
            a = TaskAttempt.query.filter_by(
                task_id=t.id, user_id=s.id
            ).first()
            if a and a.completed:
                scores[t.name] = a.score
                total += a.score
                completed += 1
                if a.completed_at:
                    if first_time is None or a.completed_at < first_time:
                        first_time = a.completed_at
            else:
                scores[t.name] = None
        rows.append({
            "username": s.username,
            "full_name": s.full_name or s.username,
            "scores": scores,
            "total": total,
            "completed": completed,
            "first_time": first_time,
        })
    rows.sort(key=lambda r: (-r["total"], r["first_time"] or datetime.max))
    return tasks, rows
