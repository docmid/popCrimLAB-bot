import os
import logging
import random
import threading
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# ─── DATA: MYTHS ──────────────────────────────────────────────────────────
MYTHS = [
    {"claim": "Кровь светится под ультрафиолетовым светом", "verdict": "МИФ",
     "explanation": "Кровь наоборот поглощает УФ-излучение — на тёмной поверхности она будет выглядеть ещё темнее. В кино путают с люминолом: это химический реагент, который наносят на поверхность, и он даёт свечение в реакции с гемоглобином."},
    {"claim": "Любая фотография с места преступления пойдёт в дело", "verdict": "МИФ",
     "explanation": "Судебная фотография — отдельная дисциплина со строгими правилами: ориентирующий, обзорный, узловой и детальный снимки с масштабной линейкой. Кадр в отражении фарного стекла — красиво для сериала, в суде бесполезен."},
    {"claim": "У однояйцевых близнецов одинаковая ДНК", "verdict": "СПОРНО",
     "explanation": "Стандартный профиль действительно может не выявить различий. Но при расширенном профилировании по большему числу локусов различия находятся — они возникают из-за ошибок при делении клеток в процессе развития."},
    {"claim": "Агата Кристи — самый финансово успешный автор детективов за всё время", "verdict": "ФАКТ",
     "explanation": "Её книги уступают по тиражам только Библии и Шекспиру. Более 2 миллиардов проданных копий на 100+ языках."},
    {"claim": "Постельный клоп может хранить ДНК укушенного человека", "verdict": "ФАКТ",
     "explanation": "До трёх дней после укуса в клопе сохраняется кровь жертвы, пригодная для ДНК-анализа."},
    {"claim": "По трупному окоченению можно точно установить время смерти", "verdict": "СПОРНО",
     "explanation": "Точность зависит от десятков факторов — температура, влажность, одежда, масса тела. Но в первые часы после смерти опытный эксперт может дать точность до часа."},
    {"claim": "Утопленника невозможно отличить от тела, брошенного в воду после смерти", "verdict": "МИФ",
     "explanation": "Чаще всего можно. Главный признак — планктон: при утоплении диатомеи попадают в лёгкие, пазухи и даже костный мозг."},
    {"claim": "Яд всегда обнаружат при вскрытии", "verdict": "МИФ",
     "explanation": "Стандартный токсикологический скрининг ищет ограниченный набор веществ. Редкие яды легко пропустить, если не знаешь что искать."},
    {"claim": "Синяки не образуются после смерти", "verdict": "МИФ",
     "explanation": "Образуются. Посмертные кровоподтёки — реальное явление, и отличить их от прижизненных бывает непросто."},
    {"claim": "По скелету невозможно определить пол", "verdict": "МИФ",
     "explanation": "Можно, и с высокой точностью. Таз, череп, размеры костей дают достаточно информации для вывода."},
    {"claim": "Следы пальцев рук на месте преступления называют «отпечатками»", "verdict": "МИФ",
     "explanation": "«Отпечатки» — только то, что занесено в дактилоскопическую карту. То, что находят на месте преступления — следы пальцев рук."},
    {"claim": "Волос без луковицы бесполезен для ДНК-анализа", "verdict": "СПОРНО",
     "explanation": "Ядерный ДНК-профиль не получить, но волос без луковицы даст мРНК, по которой можно сделать отрицательный вывод."},
    {"claim": "Почерковедческая экспертиза — точная наука", "verdict": "МИФ",
     "explanation": "Это статистическая игра с вероятностями. Вывод формулируется как «категорично», «вероятно», либо «не представляется возможным»."},
    {"claim": "Следы шин уникальны как отпечатки пальцев", "verdict": "СПОРНО",
     "explanation": "Шины с завода одной партии идентичны. Уникальность появляется позже — в процессе эксплуатации."},
    {"claim": "Гильза всегда остаётся на месте преступления", "verdict": "МИФ",
     "explanation": "При стрельбе из револьвера гильзы остаются в барабане. Из винтовок и пулемётов — могут улететь и откатиться."},
    {"claim": "Судмедэксперт работает прямо на месте преступления", "verdict": "СПОРНО",
     "explanation": "Работает в роли специалиста, но вскрытие — только в морге, в контролируемых условиях."},
    {"claim": "Эксперт ведёт дело от начала до конца", "verdict": "МИФ",
     "explanation": "Эксперт вообще не ведёт дело — это работа следователя. Эксперт лишь отвечает на конкретные вопросы."},
    {"claim": "Результаты полиграфа принимаются судом как доказательство", "verdict": "МИФ",
     "explanation": "Полиграф не является вещественным доказательством, но может влиять на процессуальные решения."},
    {"claim": "Криминалист и судмедэксперт — одна профессия", "verdict": "МИФ",
     "explanation": "Объединяющий термин — forensic scientist. Судмедэксперт, криминалист, трасолог — разные специальности."},
    {"claim": "Фоторобот даёт точное изображение преступника", "verdict": "МИФ",
     "explanation": "Фоторобот — это ориентировка, не портрет. Его цель — задать направление поиска."},
]

VERDICT_COLOR = {"МИФ": "❌", "ФАКТ": "✅", "СПОРНО": "⚠️"}

# ─── DATA: QUIZ ───────────────────────────────────────────────────────────
QUIZ = [
    {"q": "Как называется способность тканей реагировать на раздражители после смерти?",
     "options": ["Суправитальные реакции", "Аутолиз", "Ливор мортис", "Трупный спазм"], "correct": 0,
     "explanation": "Суправитальные реакции используются для определения давности смерти: чем слабее реакция, тем больше времени прошло."},
    {"q": "Почему трупное окоченение разрешается через сутки-двое?",
     "options": ["Мышцы остывают", "Разлагается мышечная ткань", "Кровь оседает вниз", "Прекращается нервная проводимость"], "correct": 1,
     "explanation": "Окоченение — связывание актина с миозином. Разрешается по мере разложения мышечной ткани."},
    {"q": "Поза боксёра на пожаре возникает потому что...",
     "options": ["Человек защищался перед смертью", "Мышцы-сгибатели сильнее разгибателей", "Высокая температура разрушает суставы", "Тело теряет воду при горении"], "correct": 1,
     "explanation": "Мышцы-сгибатели развиты сильнее — тело принимает характерную позу независимо от того, был ли человек жив."},
    {"q": "Какой орган является ключевым доказательством утопления?",
     "options": ["Лёгкие", "Почки", "Костный мозг", "Печень"], "correct": 2,
     "explanation": "В костный мозг планктон попадает только с током крови при живом кровообращении."},
    {"q": "Что исследует судебная одорология?",
     "options": ["Следы обуви", "Запаховые следы", "Состав почвы", "Звуковые записи"], "correct": 1,
     "explanation": "Судебная одорология изучает запаховые следы человека для идентификации личности."},
    {"q": "Куда выбрасывать стаканчик из-под кофе на месте происшествия?",
     "options": ["Унести с собой", "Отдать помощнику", "В специально отведённое место от следователя", "За забор вместе с перчатками"], "correct": 2,
     "explanation": "Любой посторонний предмет — источник загрязнения доказательной базы."},
    {"q": "Какие три вида следов пальцев рук выделяют по механизму образования?",
     "options": ["Мокрые, сухие, смешанные", "Видимые, слабовидимые, невидимые", "Латентные, видимые, объёмные", "Поверхностные, объёмные, цифровые"], "correct": 2,
     "explanation": "Латентные (невидимые), видимые (окрашенным веществом) и объёмные (вдавленные в пластичном материале)."},
    {"q": "Дактилоскопия и дерматоглифика — в чём разница?",
     "options": ["Это одно и то же", "Дерматоглифика — лженаука, дактилоскопия — научный метод", "Дерматоглифика точнее", "Обе используются одинаково"], "correct": 1,
     "explanation": "Дактилоскопия — научный метод идентификации. Дерматоглифика — попытка определять характер по узорам кожи. Лженаука."},
    {"q": "Что такое контактно-диффузионный метод?",
     "options": ["Способ изъятия запаховых следов", "Перенос микрочастиц при контакте", "Метод восстановления следов на влажных поверхностях", "Химический анализ следов крови"], "correct": 1,
     "explanation": "На самом деле — способ выявления металлов (медь, свинец, сурьма) путём переноса на фотобумагу."},
    {"q": "Какой материал лучше всего сохраняет следы пальцев рук?",
     "options": ["Дерево", "Ткань", "Стекло и полированные поверхности", "Бумага"], "correct": 2,
     "explanation": "Гладкие непористые поверхности лучше всего сохраняют латентные следы."},
    {"q": "Кто имеет право назначить судебно-медицинскую экспертизу?",
     "options": ["Только прокурор", "Следователь, дознаватель, суд", "Только судья", "Любой сотрудник полиции"], "correct": 1,
     "explanation": "Назначить экспертизу вправе следователь, дознаватель или суд."},
    {"q": "Что такое инсценировка в криминалистическом смысле?",
     "options": ["Реконструкция событий", "Умышленное изменение обстановки для введения следствия в заблуждение", "Фотофиксация места преступления", "Показания свидетелей"], "correct": 1,
     "explanation": "Инсценировка — имитация самоубийства, несчастного случая или кражи с целью обмануть следствие."},
]

# ─── DATA: CASE 1 (DACHA) ─────────────────────────────────────────────────
CASE1_STEPS = [
    {"text": "С чего начинаешь осмотр?", "options": [
        ("Осматриваю тело", "Мужчина сидит в кресле, голова поникшая на грудь. Кожные покровы серые. На шее — странгуляционная борозда. Трупные пятна на спине и ягодицах, окоченение разрешается."),
        ("Беру бутылку и стакан", "В стакане остатки коньяка. Бутылка початая, примерно треть выпита."),
        ("Осматриваю входную дверь", "Дверь не заперта, следов взлома нет."),
        ("Ищу телефон погибшего", "Телефон на зарядке у кресла. Последний звонок — двое суток назад."),
    ]},
    {"text": "Оцениваешь трупные явления. Какова давность смерти?", "options": [
        ("2–4 часа назад", "Ты фиксируешь в протоколе: давность 2–4 часа."),
        ("Более двух суток назад", "Разрешающееся окоченение, выраженные трупные пятна. Давность — около двух суток."),
        ("12–24 часа назад", "Ты фиксируешь в протоколе: давность 12–24 часа."),
        ("Невозможно определить", "Ты отмечаешь давность как неустановленную."),
    ]},
    {"text": "На шее странгуляционная борозда. Верёвки нигде нет. Что делаешь?", "options": [
        ("Осматриваю борозду детально", "Борозда одиночная, горизонтальная, поверхностная. Кровоизлияний в мягкие ткани нет."),
        ("Ищу следы борьбы", "Мебель не перевёрнута, следов борьбы нет."),
        ("Осматриваю воротник рубашки", "Воротник плотный. На внутренней стороне след давления, совпадающий с бороздой."),
        ("Фотографирую и иду дальше", "Борозда зафиксирована на фото."),
    ]},
    {"text": "Телевизор работает. Что делаешь?", "options": [
        ("Проверяю время последнего включения", "Смарт-ТВ: последнее включение двое суток назад в 21:14."),
        ("Смотрю какой канал", "Идёт новостной канал."),
        ("Беру следы рук с пульта", "Следы изъяты на экспертизу."),
        ("Не обращаю внимания", "Телевизор продолжает работать."),
    ]},
]
CASE1_VERDICT = {"text": "Формулируешь заключение:", "options": [
    ("Острая сердечная недостаточность, насильственный характер не установлен", True),
    ("Убийство через удушение — борозда на шее", False),
    ("Отравление алкоголем", False),
    ("Самоубийство через повешение", False),
]}

# ─── DATA: CASE 2 (HENDERSON) ─────────────────────────────────────────────
CASE2_ROUNDS = [
    {"intro": None, "options": [
        ("А. Осмотреть тело", "Под ногтями погибшего обнаружены частицы кожи. На костяшках пальцев свежие повреждения. Перед смертью он явно дрался с нападавшим."),
        ("Б. Осмотреть автомобиль", "На двери обнаружен отпечаток подошвы дорогой мужской обуви."),
        ("В. Проверить телефон погибшего", "За два часа до смерти Марк получил сообщение: «Нам нужно встретиться. Сегодня всё решится»."),
        ("Г. Проверить финансовые документы", "Три дня назад на счёт поступило 50 000 долларов. Источник неизвестен."),
    ]},
    {"intro": None, "options": [
        ("А. Проверить ДНК под ногтями", "Обнаружен мужской профиль ДНК. В базе совпадений нет."),
        ("Б. Изучить происхождение денежных средств", "Деньги поступили через юридическую фирму."),
        ("В. Получить записи камер наблюдения", "За несколько часов до убийства за Марком следил неизвестный мужчина."),
        ("Г. Изучить судебное дело", "Через два дня Марк должен был дать новые показания, отличающиеся от прежних."),
    ]},
    {"intro": "Появляются подозреваемые: адвокат Браун, бизнесмен Кейн, детектив Росс, бывшая жена Сара.", "options": [
        ("А. Проверить адвоката Брауна", "Между ним и Марком произошёл конфликт. Браун требовал придерживаться первоначальных показаний."),
        ("Б. Проверить бизнесмена Кейна", "Если бы Марк изменил показания, Кейн мог потерять контракт и стать фигурантом дела."),
        ("В. Установить личность человека с камер", "Это частный детектив Майкл Росс."),
        ("Г. Допросить бывшую жену", "У Сары есть подтверждённое алиби на ночь убийства."),
    ]},
    {"intro": None, "options": [
        ("А. Проверить обувь со следа", "Дорогой итальянский бренд. Такую обувь носит адвокат Браун."),
        ("Б. Повторно изучить данные о переводе", "Перевод оформлен через юридическую фирму Брауна."),
        ("В. Допросить детектива Росса", "Росс признаёт слежку. Заказчиком выступал Томас Кейн."),
        ("Г. Восстановить удалённые сообщения", "Последняя встреча назначена человеком, связанным с Кейном."),
    ]},
]
CASE2_FINAL = [
    ("А. Срочно арестовать адвоката", "Вы переходите к финалу."),
    ("Б. Проверить происхождение ДНК", "Образец принадлежит сотруднику охраны компании Кейна."),
    ("В. Проверить маршрут Кейна", "В ночь убийства его автомобиль находился рядом с местом преступления."),
    ("Г. Изучить контакты детектива", "В день убийства Росс связывался с Кейном."),
]
CASE2_SUSPECTS = [
    ("brown", "Адвоката Брауна"),
    ("kane", "Бизнесмена Кейна"),
    ("ross", "Детектива Росса"),
    ("sara", "Бывшую жену Сару"),
]
CASE2_ENDINGS = {
    "brown": (False, "🔴 Дело закрыто без приговора", "Дополнительные экспертизы исключают участие Брауна. Настоящий убийца исчезает."),
    "ross": (False, "🔴 Исполнитель арестован, заказчик на свободе", "Вы арестовали исполнителя слежки, но не доказали его участие в убийстве."),
    "sara": (False, "🔴 Версия развалилась в суде", "Алиби Сары подтверждается полностью."),
    "kane": (True, "🟢 Дело раскрыто!", "Вы доказали мотив, организацию встречи, связь со слежкой и присутствие у места преступления. Убийца установлен — Томас Кейн."),
}

# ─── USER STATE (in-memory) ───────────────────────────────────────────────
user_state = {}

def get_state(user_id):
    if user_id not in user_state:
        user_state[user_id] = {}
    return user_state[user_id]

# ─── HANDLERS ──────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_menu(update, context)

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎬 Реально или нет?", callback_data="menu_myth")],
        [InlineKeyboardButton("🧠 Викторина", callback_data="menu_quiz")],
        [InlineKeyboardButton("🔍 Дело открыто", callback_data="menu_case_select")],
    ]
    text = "👋 Я popCrimLAB — бот канала про криминалистику.\n\nВыбери режим:"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id
    state = get_state(user_id)

    # ── MENU ──
    if data == "menu_main":
        await show_menu(update, context)
        return

    # ── MYTH MODE ──
    if data == "menu_myth":
        state["myth_queue"] = random.sample(MYTHS, 7)
        state["myth_idx"] = 0
        state["myth_score"] = 0
        await send_myth(query, state)
        return

    if data.startswith("myth_answer_"):
        answer = data.replace("myth_answer_", "")
        myth = state["myth_queue"][state["myth_idx"]]
        verdict_map = {"true": "ФАКТ", "myth": "МИФ", "mixed": "СПОРНО"}
        is_correct = verdict_map.get(answer) == myth["verdict"]
        if is_correct:
            state["myth_score"] += 1
        result_emoji = "✅ Верно!" if is_correct else f"❌ Неверно — это {myth['verdict']}"
        text = f"«{myth['claim']}»\n\n{result_emoji}\n\n{myth['explanation']}"
        state["myth_idx"] += 1
        if state["myth_idx"] < len(state["myth_queue"]):
            keyboard = [[InlineKeyboardButton("Следующее →", callback_data="myth_next")],
                        [InlineKeyboardButton("← В меню", callback_data="menu_main")]]
        else:
            score = state["myth_score"]
            text += f"\n\n🏁 Результат: {score} / 7"
            keyboard = [[InlineKeyboardButton("🔄 Хочу ещё", callback_data="menu_myth")],
                        [InlineKeyboardButton("← В меню", callback_data="menu_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == "myth_next":
        await send_myth(query, state)
        return

    # ── QUIZ MODE ──
    if data == "menu_quiz":
        state["quiz_queue"] = random.sample(QUIZ, len(QUIZ))
        state["quiz_idx"] = 0
        state["quiz_score"] = 0
        await send_quiz(query, state)
        return

    if data.startswith("quiz_answer_"):
        idx = int(data.replace("quiz_answer_", ""))
        q = state["quiz_queue"][state["quiz_idx"]]
        is_correct = idx == q["correct"]
        if is_correct:
            state["quiz_score"] += 1
        result = "✅ Верно!" if is_correct else f"❌ Неверно. Правильный ответ: {q['options'][q['correct']]}"
        text = f"{q['q']}\n\n{result}\n\n{q['explanation']}"
        state["quiz_idx"] += 1
        if state["quiz_idx"] < len(state["quiz_queue"]):
            keyboard = [[InlineKeyboardButton("Следующий →", callback_data="quiz_next")],
                        [InlineKeyboardButton("← В меню", callback_data="menu_main")]]
        else:
            text += f"\n\n🏁 Результат: {state['quiz_score']} / {len(state['quiz_queue'])}"
            keyboard = [[InlineKeyboardButton("← В меню", callback_data="menu_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == "quiz_next":
        await send_quiz(query, state)
        return

    # ── CASE SELECT ──
    if data == "menu_case_select":
        keyboard = [
            [InlineKeyboardButton("🏡 Дело №1: Дача", callback_data="case1_start")],
            [InlineKeyboardButton("🌃 Дело №17: Последние показания", callback_data="case2_start")],
            [InlineKeyboardButton("← В меню", callback_data="menu_main")],
        ]
        await query.edit_message_text("Выбери дело для расследования 👇", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # ── CASE 1 ──
    if data == "case1_start":
        state["c1_step"] = 0
        state["c1_clues"] = []
        text = ("🔍 Дело №1: Дача\n\n"
                "Субботнее утро. Соседи вызвали полицию — два дня никто не выходит, собака воет. "
                "Дверь не заперта. В кресле у телевизора — мужчина, 60 лет. На столике бутылка коньяка, "
                "стакан, таблетки от давления. Телевизор работает.\n\n"
                "⚠️ Дело состоит из 5 этапов. На каждом — один выбор, остальное будет недоступно. Решай взвешенно.")
        keyboard = [[InlineKeyboardButton("▶️ Приступить", callback_data="case1_q_0")],
                    [InlineKeyboardButton("← В меню", callback_data="menu_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("case1_q_"):
        step_idx = int(data.replace("case1_q_", ""))
        state["c1_step"] = step_idx
        await send_case1_step(query, state, step_idx)
        return

    if data.startswith("case1_pick_"):
        _, _, step_idx, opt_idx = data.split("_")
        step_idx, opt_idx = int(step_idx), int(opt_idx)
        label, info = CASE1_STEPS[step_idx]["options"][opt_idx]
        state.setdefault("c1_clues", []).append(info)
        clues_text = "\n".join(f"📋 {c}" for c in state["c1_clues"])
        text = f"{clues_text}\n\n✅ {label}\n{info}"
        next_step = step_idx + 1
        if next_step < len(CASE1_STEPS):
            keyboard = [[InlineKeyboardButton("Продолжить →", callback_data=f"case1_q_{next_step}")]]
        else:
            keyboard = [[InlineKeyboardButton("Перейти к выводу →", callback_data="case1_verdict")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == "case1_verdict":
        clues_text = "\n".join(f"📋 {c}" for c in state.get("c1_clues", []))
        text = f"{clues_text}\n\n❓ {CASE1_VERDICT['text']}"
        keyboard = [[InlineKeyboardButton(opt[0], callback_data=f"case1_v_{i}")] for i, opt in enumerate(CASE1_VERDICT["options"])]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("case1_v_"):
        idx = int(data.replace("case1_v_", ""))
        label, is_correct = CASE1_VERDICT["options"][idx]
        if is_correct:
            text = f"🟢 Верное заключение!\n\nТы правильно интерпретировал улики и пришёл к верному выводу. Так держать."
            keyboard = [[InlineKeyboardButton("← В меню", callback_data="menu_main")]]
        else:
            text = f"🔴 Дело закрыто с ошибкой\n\nТвоё заключение не совпало с тем, что показала экспертиза. Попробуй ещё раз — улики были на месте."
            keyboard = [[InlineKeyboardButton("🔄 Переиграть", callback_data="case1_start")],
                        [InlineKeyboardButton("← В меню", callback_data="menu_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # ── CASE 2: HENDERSON ──
    if data == "case2_start":
        state["c2_round"] = 0
        state["c2_picked"] = []
        state["c2_clues"] = []
        text = ("🌃 Дело №17: Последние показания\n\n"
                "03:17 ночи. На пустынной парковке возле бизнес-центра обнаружено тело мужчины — "
                "Марк Хендерсон, 38 лет. Смерть от удара тупым предметом, признаки борьбы, вещи не похищены. "
                "Хендерсон был свидетелем по резонансному делу.\n\n"
                "В каждом раунде выбери ДВА действия из четырёх.")
        keyboard = [[InlineKeyboardButton("▶️ Начать расследование", callback_data="case2_round_0")],
                    [InlineKeyboardButton("← В меню", callback_data="menu_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("case2_round_"):
        round_idx = int(data.replace("case2_round_", ""))
        state["c2_round"] = round_idx
        state["c2_picked"] = []
        await send_case2_round(query, state, round_idx)
        return

    if data.startswith("case2_pick_"):
        _, _, round_idx, opt_idx = data.split("_")
        round_idx, opt_idx = int(round_idx), int(opt_idx)
        label, info = CASE2_ROUNDS[round_idx]["options"][opt_idx]
        state["c2_picked"].append(opt_idx)
        state.setdefault("c2_clues", []).append(info)
        if len(state["c2_picked"]) < 2:
            await send_case2_round(query, state, round_idx)
        else:
            clues_text = "\n".join(f"📋 {c}" for c in state["c2_clues"])
            next_round = round_idx + 1
            if next_round < len(CASE2_ROUNDS):
                text = f"{clues_text}\n\n✅ Раунд {round_idx+1} завершён."
                keyboard = [[InlineKeyboardButton("Следующий раунд →", callback_data=f"case2_round_{next_round}")]]
            else:
                text = f"{clues_text}\n\n✅ Все раунды собраны. Переходим к финалу."
                keyboard = [[InlineKeyboardButton("К финалу →", callback_data="case2_final")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == "case2_final":
        clues_text = "\n".join(f"📋 {c}" for c in state.get("c2_clues", []))
        text = f"{clues_text}\n\n🔎 Последнее действие. Выберите ОДНО:"
        keyboard = [[InlineKeyboardButton(opt[0], callback_data=f"case2_final_{i}")] for i, opt in enumerate(CASE2_FINAL)]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("case2_final_"):
        idx = int(data.replace("case2_final_", ""))
        label, info = CASE2_FINAL[idx]
        clues_text = "\n".join(f"📋 {c}" for c in state.get("c2_clues", []))
        text = f"{clues_text}\n\n✅ {label}\n{info}\n\n⚖️ Кого вы обвиняете?"
        keyboard = [[InlineKeyboardButton(label2, callback_data=f"case2_accuse_{sid}")] for sid, label2 in CASE2_SUSPECTS]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("case2_accuse_"):
        suspect_id = data.replace("case2_accuse_", "")
        win, title, desc = CASE2_ENDINGS[suspect_id]
        text = f"{title}\n\n{desc}"
        if win:
            keyboard = [[InlineKeyboardButton("← В меню", callback_data="menu_main")]]
        else:
            keyboard = [[InlineKeyboardButton("🔄 Переиграть с начала", callback_data="case2_start")],
                        [InlineKeyboardButton("← В меню", callback_data="menu_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return


async def send_myth(query, state):
    myth = state["myth_queue"][state["myth_idx"]]
    n = state["myth_idx"] + 1
    total = len(state["myth_queue"])
    text = f"🎬 Реально или нет? ({n}/{total})\n\n«{myth['claim']}»\n\nКак думаешь?"
    keyboard = [
        [InlineKeyboardButton("✅ Правда", callback_data="myth_answer_true")],
        [InlineKeyboardButton("❌ Миф", callback_data="myth_answer_myth")],
        [InlineKeyboardButton("⚠️ Спорно", callback_data="myth_answer_mixed")],
        [InlineKeyboardButton("← В меню", callback_data="menu_main")],
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def send_quiz(query, state):
    q = state["quiz_queue"][state["quiz_idx"]]
    n = state["quiz_idx"] + 1
    text = f"🧠 Вопрос {n} из {len(state['quiz_queue'])}\n\n{q['q']}"
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"quiz_answer_{i}")] for i, opt in enumerate(q["options"])]
    keyboard.append([InlineKeyboardButton("← В меню", callback_data="menu_main")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def send_case1_step(query, state, step_idx):
    step = CASE1_STEPS[step_idx]
    clues = state.get("c1_clues", [])
    clues_text = "\n".join(f"📋 {c}" for c in clues)
    prefix = f"{clues_text}\n\n" if clues_text else ""
    text = f"{prefix}❓ {step['text']}"
    keyboard = [[InlineKeyboardButton(opt[0], callback_data=f"case1_pick_{step_idx}_{i}")] for i, opt in enumerate(step["options"])]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def send_case2_round(query, state, round_idx):
    round_data = CASE2_ROUNDS[round_idx]
    picked = state.get("c2_picked", [])
    clues = state.get("c2_clues", [])
    clues_text = "\n".join(f"📋 {c}" for c in clues)
    remaining_needed = 2 - len(picked)
    intro = f"\n{round_data['intro']}\n" if round_data["intro"] else ""
    text = f"{clues_text}\n\n🔎 Раунд {round_idx+1} — выбери {remaining_needed} действие(я){intro}"
    keyboard = []
    for i, opt in enumerate(round_data["options"]):
        if i not in picked:
            keyboard.append([InlineKeyboardButton(opt[0], callback_data=f"case2_pick_{round_idx}_{i}")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


import asyncio

def run_bot():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is not set")
    # Background threads don't have an event loop by default — create one.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    logger.info("Bot starting...")
    app.run_polling(close_loop=False, stop_signals=None)


# ─── MINIMAL WEB SERVER (so Render Web Service stays happy) ──────────────
flask_app = Flask(__name__)

@flask_app.route("/")
def health():
    return "popCrimLAB bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    # Run the Telegram bot in a background thread,
    # and the tiny Flask server in the main thread (Render needs an open port).
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    run_flask()
