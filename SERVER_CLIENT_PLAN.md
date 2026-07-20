# Kung-Fu Chess — תוכנית ארכיטקטורה ופיתוח שרת–לקוח

## 1. מטרת המסמך

מסמך זה מגדיר את הדרך להפוך את משחק ה־Kung-Fu Chess הקיים ממשחק מקומי למשחק רשת מבוסס שרת–לקוח.

המטרה היא לבנות מערכת:

- נקייה וברורה מבחינת אחריות של כל שכבה.
- פשוטה מספיק לפרויקט לימודי ולהתקדמות הדרגתית.
- יציבה, ניתנת לבדיקה, ואינה שוברת את המשחק המקומי הקיים.
- מוכנה להרחבות עתידיות כמו משחקים מקבילים, חדרים, צופים, משתמשים ומסדי נתונים אחרים.
- ללא Over-engineering מוקדם.

העיקרון המנחה:

> מתכננים מראש את הדרך כולה, אך בכל שלב מממשים רק את המינימום הנדרש כדי שהשלב יעבוד היטב, ייבדק ויישאר פתוח להמשך.

---

## 2. המצב הקיים

כרגע המשחק עובד במצב מקומי:

```text
Mouse / Keyboard
       ↓
Input Controller
       ↓
GameEngine
       ↓
GameSnapshot
       ↓
Renderer / OpenCV
```

שני השחקנים משחקים באותו מחשב, באותו חלון ומול אותו מופע של `GameEngine`.

ליבת המשחק כבר מופרדת יחסית מה־UI:

- `model/` — מודל הלוח והכלים.
- `rules/` — חוקי התנועה והמשחק.
- `realtime/` — תנועה בזמן אמת, זמן, קפיצות וקירורים.
- `engine/` — תזמור המשחק ויצירת Snapshot.
- `view/` — ציור בלבד.
- `input/` — קלט משתמש והמרה לפעולות.

מכיוון שהליבה אינה אמורה להיות תלויה ב־OpenCV, WebSocket או SQLite, אפשר להשתמש בה גם בתוך השרת בלי לכתוב מחדש את חוקי המשחק.

---

## 3. תמונת היעד

במצב הרשת השרת יהיה מקור האמת היחיד.

```text
Client White                    Server                    Client Black
────────────                    ──────                    ────────────
Input                           Match                     Input
View                            GameEngine                View
NetworkClient   ← WebSocket →   GameLoop   ← WebSocket →  NetworkClient
Snapshot cache                  Board                     Snapshot cache
```

### השרת אחראי על

- מצב המשחק האמיתי.
- `GameEngine` ו־`Board`.
- בדיקת חוקיות מהלכים.
- קידום הזמן במשחק.
- שיוך שחקנים לצבעים.
- משחקים וחדרים.
- התחברות משתמשים.
- דירוג ELO.
- Matchmaking.
- ניתוקים וחיבור מחדש.
- שמירה ב־SQLite.
- שידור מצב ועדכונים ללקוחות המתאימים.

### הלקוח אחראי על

- קבלת קלט מהמשתמש.
- שליחת בקשות לשרת.
- קבלת Snapshot ואירועים.
- ציור המשחק.
- אנימציות, צלילים ו־HUD.
- הצגת הודעות שגיאה, חדר, דירוג וספירה לאחור.

### כלל יסוד

```text
Client לא משנה Board.
Client לא בודק חוקי שחמט.
Client לא מפעיל GameEngine אמיתי במשחק רשת.
Server לא מצייר עם OpenCV.
GameEngine לא מכיר sockets, users, rooms או SQLite.
```

---

## 4. דרישות הפרויקט לפי שלבים

| שלב | דרישה |
|---|---|
| A | Pub/Sub Bus עבור ניקוד, לוג מהלכים, צלילים ואנימציות התחלה/סיום |
| B | שרת מקומי בתהליך יחיד עם WebSocket; לקוח שולח פקודות ומקבל מצב משחק |
| C | שם משתמש בלבד דרך Shell; שני שחקנים, הראשון לבן והשני שחור |
| D | שם משתמש וסיסמה, SQLite בצד השרת, דירוג התחלתי 1200 ועדכון ELO |
| E | Play ו־Matchmaking בטווח ±100 ELO; המתנה עד דקה; ניתוק מוביל ל־resign לאחר 20 שניות |
| F | Create/Join Room, מזהה חדר, צופים, לוגים בצד השרת והלקוח |

כל שלב נשען על השלב הקודם. אין לממש את כל המערכת בבת אחת.

מבנה התוכנית בהמשך תואם בדיוק למצגת: **A, B, C, D, E, F**. כאשר שלב דורש כמה פעולות מימוש, הן מופיעות כצעדים פנימיים של אותו שלב ולא כשלבים עצמאיים.

---

## 5. החלטות ארכיטקטוניות מרכזיות

### 5.1 השרת הוא Authoritative

כל פעולה שמשנה מצב עוברת דרך השרת:

```text
Client request
    ↓
Server validates identity and permissions
    ↓
GameEngine move_from_to / jump
    ↓
Game state changes
    ↓
Server create_snapshot
    ↓
Broadcast to clients of the same game
```

הלקוח רשאי לבצע בדיקות UI נוחות, אך הן אינן מחליפות את בדיקת השרת.

> API מקומי קיים: `select` + `move_request(target)` (two-click UI), `jump(position)`, `tick(ms)`, `create_snapshot()`.
> לנתיב הרשת משתמשים ב־`move_from_to(src, dst)` — ראו סעיף 5.7.

### 5.2 ליבת המשחק נשארת עצמאית

אין להעביר לתוכה:

- WebSocket.
- JSON.
- asyncio.
- משתמשים וסיסמאות.
- game IDs או room IDs.
- SQLite.
- קוד GUI.

שינויים בליבה יבוצעו רק כאשר חסר API משחקי אמיתי, לדוגמה אירוע `GameOverEvent` או פעולה מפורשת של `resign`.

### 5.3 משחק אחד הוא יחידת בידוד

גם כשבשלב הראשון קיים רק משחק אחד, לא נבנה שרת עם `global_engine`.

נשתמש במושג `Match`:

```text
Match
├── game_id
├── GameEngine
├── players
├── spectators
├── EventBus
├── broadcaster
├── tick task
└── lock
```

בשלב הראשון יהיה Match יחיד בשם `default`. בהמשך אותו מבנה יתמוך בהרבה משחקים ללא שינוי יסודי.

### 5.4 הפרדה בין Domain Events לבין Network Messages

אירוע פנימי במשחק אינו הודעת רשת.

```text
GameEngine event
      ↓
Match / Broadcaster translates
      ↓
Network message
```

לדוגמה:

```text
MoveResolvedEvent
      ↓
{"type": "game_event", "kind": "move_resolved", ...}
```

כך ה־Engine אינו תלוי בפורמט התקשורת.

### 5.5 פרוטוקול ברור ומרוכז

כל קידוד ופענוח הודעות יישבו במקום אחד.

אין לפזר `json.loads`, בדיקות שדות ומחרוזות פקודה בכל השרת.

המלצה: JSON עם שדה `type` ו־`payload`.

```json
{
  "type": "move_request",
  "game_id": "default",
  "payload": {
    "from_row": 6,
    "from_col": 4,
    "to_row": 4,
    "to_col": 4
  }
}
```

פורמט טקסט כמו `WQe2e5` אפשרי, אך JSON יהיה ברור יותר להרחבות של Login, Rooms ו־Matchmaking.

### 5.6 שומרים על המצב המקומי

ה־Hot Seat הקיים לא יימחק.

יהיו שתי דרכי הרצה:

```text
Local session  → GameEngine ישירות
Remote session → Network client מול Server
```

שתי הדרכים ישתמשו באותו View ככל האפשר.

### 5.7 החלטה: API מהלך מלא לשרת — `move_from_to`

ה־`GameEngine` המקומי בנוי ל־UI של שני קליקים: `select(src)` ואז `move_request(dst)`. זה מתאים ל־`input/Controller`, אך **לא** לפרוטוקול רשת שבו הלקוח שולח מקור ויעד בפקודה אחת.

**החלטה:** מוסיפים לליבה מתודה מפורשת:

```python
move_from_to(src, dst) -> None
```

- מבצעת בחירה + אימות + התחלת תנועה באופן אטומי.
- אינה משאירה `selected` "תלוי" בין בקשות רשת.
- `select` / `move_request` נשארים ל־hot-seat ול־Controller הקיים.

חלופה שנדחתה: `engine.select(src); engine.move_request(dst)` תחת lock בשרת — שברירית (בחירה עלולה להישאר אם הבקשה נכשלת חלקית) ומערבבת מצב UI בליבת המשחק.

### 5.8 `selected_cell` ברשת

במצב remote, בחירת משבצת היא מצב UI מקומי לכל לקוח. השרת אינו משדר `selected_cell` כ־authoritative בין שחקנים (מנקים בשכבת ה־serializer / שולחים `null`).

---

## 6. מבנה תיקיות יעד מאוזן

המבנה הסופי המתוכנן:

```text
project/
├── model/                       # קיים — ללא תלות ברשת
├── rules/                       # קיים
├── realtime/                    # קיים
├── engine/                      # קיים; GameEngine + events (domain)
├── snapshots/                   # קיים — GameSnapshot / PieceSnapshot / MoveRecord (headless)
├── bus/                         # חדש שלב A — EventBus גנרי
├── board_io/                    # קיים (לא boardio/)
├── input/                       # קיים; קלט מקומי/GUI
├── view/                        # קיים; ציור בלבד + GameRunner
│
├── shared/                      # פורמט מידע משותף ללקוח ולשרת
│   ├── message_types.py
│   ├── protocol.py
│   └── serialization.py
│
├── server/
│   ├── main.py                  # Composition root והפעלת השרת
│   ├── game_server.py           # פתיחת WebSocket וחיי חיבור
│   ├── client_session.py        # מידע על חיבור אחד
│   ├── match.py                 # משחק רשת אחד
│   ├── game_registry.py         # game_id -> Match
│   ├── game_command_handler.py  # ניתוב בקשות משחק
│   ├── broadcaster.py           # שידור ללקוחות של Match מסוים
│   ├── auth_service.py          # שלב D
│   ├── elo.py                   # שלב D
│   ├── matchmaker.py            # שלב E
│   ├── room_manager.py          # שלב F
│   ├── config.py
│   └── dal/
│       ├── database.py
│       └── repositories.py
│
├── client/
│   ├── main.py
│   ├── local_session.py
│   ├── remote_session.py
│   ├── network_client.py
│   ├── remote_game_proxy.py
│   ├── client_state.py
│   ├── cli_login.py             # שלבים C/D
│   └── room_dialog.py           # שלב F
│
└── tests/
    ├── unit/
    └── integration/
```

### הערה חשובה

לא יוצרים את כל הקבצים ביום הראשון.

כל קובץ ייווצר רק כאשר השלב הנוכחי זקוק לו.

---

## 7. כללי תלות

### מותר

```text
view/       → snapshots / client state
client/     → shared/
server/     → shared/, engine/, model/, snapshots/
engine/     → rules/, realtime/, model/, snapshots/, bus/
server/dal/ → sqlite3
```

### אסור

```text
engine/  → server/
engine/  → client/
engine/  → sqlite3
engine/  → websockets
model/   → view/
server/  → cv2
view/    → rules/
client/  → RuleEngine
```

### אחריות שכבות

| שכבה | אחריות |
|---|---|
| Domain/Game Core | חוקי משחק ומצב משחק בלבד |
| Server Application | משתמשים, משחקים, הרשאות ותזמור |
| Transport | WebSocket, parsing ושליחת הודעות |
| DAL | קריאה וכתיבה למסד נתונים בלבד |
| Client | תקשורת, מצב תצוגה וקלט |
| View | ציור בלבד |

---

# 8. תוכנית המימוש

## הכנה מקדימה — בדיקת מוכנות הליבה

### מטרה

לוודא שה־GameEngine יכול לפעול ללא חלון וללא קלט פיקסלים.

### נבדוק

- אפשר ליצור `GameEngine` מתוך Board התחלתי (`board_io.BoardParser` + `engine.GameEngine`).
- אפשר לבצע `move_request` / `jump` בקואורדינטות לוח; לנתיב רשת — `move_from_to`.
- אפשר לקדם זמן עם `tick(ms)` ללא `cv2.waitKey` (`wait` הוא alias תואם־לאחור ל־`tick`).
- אפשר לקבל `GameSnapshot` מלא ו־read-only מ־`create_snapshot()` (חבילת `snapshots/`).
- ה־Snapshot אינו מכיל אובייקטים שאינם ניתנים לסריאליזציה.
- הטסטים הקיימים נשארים ירוקים.

### שינויים אפשריים בלבד

- השלמת `GameSnapshot` ו־`PieceSnapshot` ב־`snapshots/`.
- הוספת `winner` / `get_winner()` אם אינו קיים.
- הוספת `move_from_to(src, dst)` לנתיב רשת (סעיף 5.7).
- הוספת `resign(color)` רק כאשר מגיעים לשלב הניתוקים.
- הוספת `EventBus` + `GameOverEvent` (ואירועי lifecycle נוספים) בשלב A.

### לא עושים

- לא מעבירים תיקיות קיימות.
- לא מכניסים ידע על שרת לליבה.
- לא משנים את חוקי המשחק.

### תנאי סיום

```text
כל הטסטים הקיימים עוברים
+
טסט headless יוצר משחק, מבצע מהלך, מקדם זמן ומקבל Snapshot
```

---

## שלב A — Pub/Sub Bus

### מטרה

לאפשר למספר רכיבים להגיב לאירועי משחק בלי שה־GameEngine יכיר אותם.

### אירועים נדרשים

- `GameStartedEvent`
- `MotionStartedEvent`
- `JumpStartedEvent`
- `MoveResolvedEvent` / `ArrivalEvent`
- `GameOverEvent`

אין חובה שכל האירועים יפורסמו מאותה שכבה:

- אירועי משחק פנימיים — מתוך ה־Engine.
- התחלת Match רשת — מתוך `Match` או שירות השרת.

### צרכנים

- Score.
- Moves Log.
- Sound Player.
- Start animation.
- Game-over animation.

### API מינימלי

```python
subscribe(event_type, handler)
publish(event)
unsubscribe(event_type, handler)  # רק אם נדרש לניקוי Match
```

### בדיקות

- Subscriber מתאים מקבל אירוע פעם אחת.
- Subscriber מסוג אחר אינו מקבל אותו.
- מספר Subscribers מקבלים אותו אירוע.
- GameEngine ממשיך לעבוד גם כשאין Subscribers.
- שגיאה ב־Subscriber אחד אינה שוברת את מצב המשחק, בהתאם להחלטה מתועדת.

### תנאי סיום

אירוע Game Over מעדכן בפועל לפחות שני רכיבים נפרדים בלי קריאה ישירה מה־Engine אליהם.

---

## שלב B — שרת מקומי יחיד־תהליך ותקשורת WebSocket

### B.1 — WebSocket מינימלי

#### מטרה

להוכיח תקשורת בסיסית לפני הכנסת המשחק.

#### קבצים ראשונים

```text
shared/protocol.py
server/main.py
server/game_server.py
client/network_client.py
client/main.py
```

#### תרחיש

```text
Client connects
Client sends ping
Server sends pong
Client disconnects cleanly
```

#### בדיקות

- התחברות ל־localhost.
- הודעה תקינה.
- הודעה לא תקינה מחזירה error ולא מפילה את השרת.
- ניתוק לקוח לא סוגר את השרת.

#### תנאי סיום

שרת ולקוח אמיתיים מתקשרים ב־WebSocket בלי תלות ב־GameEngine.

---

### B.2 — משחק אחד בשרת ולקוח טקסטואלי אחד

#### מטרה

להעביר את מקור האמת לשרת.

#### רכיבים

```text
Match
GameRegistry
GameCommandHandler
SnapshotSerializer
```

#### התנהגות

- השרת יוצר Match בשם `default`.
- ה־Match מחזיק `GameEngine` משלו.
- הלקוח שולח `move_request` או `jump_request`.
- השרת קורא ל־GameEngine.
- השרת מחזיר `request_result` ו־`state_snapshot`.

#### הרשאות זמניות

בשלב זה אפשר לתת ללקוח אחד לבצע את שני הצבעים לצורך בדיקת התשתית בלבד.

#### תנאי סיום

לקוח טקסטואלי שולח מהלך, הזמן מתקדם בשרת, והוא מקבל Snapshot מעודכן.

---

### B.3 — לולאת הזמן של השרת

#### מטרה

להבטיח שתנועות בזמן אמת ממשיכות גם ללא הודעות חדשות מהלקוחות.

#### עיקרון

לכל Match יש Task משלו:

```text
while match is active:
    sleep(TICK_MS)
    engine.tick(elapsed_ms)
    if state changed:
        broadcast snapshot/events
```

#### כללים

- משתמשים בזמן שחלף בפועל או בטיק יציב לפי החלטת הפרויקט.
- אין להפעיל `engine.tick` מתוך כל Client בנפרד.
- Match הוא הבעלים היחיד של שעון המשחק.
- כל שינוי ב־Engine עובר דרך מנגנון סדרתי או lock של אותו Match.

#### בדיקות

- כלי מגיע ליעד גם ללא הודעה נוספת.
- שני משחקים מדומים מקדמים זמן בנפרד.
- סגירת Match עוצרת את ה־tick task.

#### תנאי סיום

מהלך בזמן אמת מסתיים בצורה נכונה כאשר הלקוחות אינם שולחים דבר.

---

### B.4 — שני Clients ושידור מצב

#### מטרה

שני לקוחות רואים את אותו משחק.

#### התנהגות

- שני חיבורים משויכים ל־`default`.
- כל שינוי משודר לשני החיבורים.
- הודעות של Match אחד אינן מגיעות ל־Match אחר.
- ה־Broadcaster שייך ל־Match ולא לשרת כולו.

#### בדיקות

- Client A מבצע מהלך.
- Client A ו־Client B מקבלים אותו sequence/snapshot.
- Client ממשחק אחר אינו מקבל את העדכון.

#### תנאי סיום

שני Clients טקסטואליים שומרים מצב מסונכרן.

---

### B.5 — חיבור ה־UI הקיים ללקוח הרשת

#### מטרה

להשתמש באותו View בלי לתת לו GameEngine אמיתי.

#### רכיבים

- `RemoteSession` — מנהלת משחק רשת בצד הלקוח.
- `NetworkClient` — send/receive.
- `ClientState` — מחזיק Snapshot אחרון ומידע UI.
- `RemoteGameProxy` — אופציונלי, רק אם הוא מפשט את החיבור ל־Controller הקיים.

#### החלטה

אין לבנות Proxy שמחקה בכוח כל פרט ב־GameEngine אם הדבר יוצר API מלאכותי.

עדיפות:

```text
Input Controller → RemoteSession.send_action(...)
Renderer         → ClientState.snapshot
```

Proxy ישמש רק אם הוא מאפשר לשמור קוד קיים בלי להסתיר התנהגות מסוכנת.

#### תנאי סיום

שני חלונות OpenCV נפרדים מציגים אותו משחק מהשרת.

---

## שלב C — שם משתמש והקצאת צבע

### מטרה

לזהות שני שחקנים ולהגביל פעולות לפי צבע.

### התנהגות

- לפני כניסה למשחק הלקוח מזין username ב־Shell.
- השרת מקבל `identify`.
- הראשון שנכנס למשחק = White.
- השני = Black.
- חיבור שלישי מקבל `server_full` בשלב זה.
- שחקן רשאי לשלוח פעולה רק עבור הכלים בצבע שלו.

### `ClientSession`

```text
connection_id
username
assigned_color
game_id
role
```

### בדיקות

- הראשון לבן והשני שחור.
- לבן אינו מזיז כלי שחור.
- שחור אינו מזיז כלי לבן.
- username ריק או לא תקין נדחה.
- ניתוק מנקה את החיבור בלי להשאיר reference שבור.

### תנאי סיום

שני משתמשים מזוהים משחקים כל אחד רק בצבע שלו.

---

## שלב D — סיסמה, SQLite ודירוג ELO

### D.1 — DAL ו־SQLite

#### מטרה

להוסיף Persistence בלי לערבב SQL בלוגיקת השרת.

#### מבנה

```text
server/dal/database.py
server/dal/repositories.py
```

#### `database.py`

- פתיחת connection.
- יצירת schema.
- ניהול transaction בסיסי.
- הגדרת row factory.

#### Repositories

- `UserRepository`
- `GameRepository`

#### טבלאות בסיסיות

```text
users
─────
id
username UNIQUE
password_hash
rating DEFAULT 1200
created_at

 games
─────
id
white_user_id
black_user_id
winner_color
started_at
ended_at

rating_changes
──────────────
id
game_id
user_id
rating_before
rating_after
UNIQUE(game_id, user_id)
```

#### כללים

- SQL קיים רק ב־DAL.
- Repository מחזיר DTO/ערכים פשוטים, לא cursor.
- בדיקות משתמשות ב־SQLite בזיכרון.

#### תנאי סיום

אפשר ליצור משתמש, לקרוא אותו ולעדכן דירוג דרך Repository בלבד.

---

### D.2 — הרשמה והתחברות

#### מטרה

להפוך את ה־username הזמני לחשבון משתמש אמיתי.

#### `AuthService`

- `register(username, password)`
- `login(username, password)`
- validation בסיסי.
- hashing מאובטח.

#### כללים

- לא שומרים סיסמה גלויה.
- לא מדפיסים סיסמה ללוגים.
- WebSocket handler אינו בודק סיסמה בעצמו.
- לאחר login, ה־ClientSession מקבל `user_id`.

#### בדיקות

- הרשמה מוצלחת.
- username כפול נדחה.
- סיסמה שגויה נדחית.
- hash שונה מהסיסמה המקורית.
- דירוג ראשוני הוא 1200.

#### תנאי סיום

שני לקוחות יכולים להירשם ולהתחבר מחדש מול SQLite.

---

### D.3 — ELO ושמירת תוצאות

#### מטרה

לעדכן דירוג בסיום משחק.

#### `elo.py`

פונקציה טהורה:

```python
calculate_new_ratings(white_rating, black_rating, result, k=32)
```

#### כללים

- עדכון מתבצע רק פעם אחת לכל משחק.
- משחק לא מדורג אינו משנה ELO.
- שמירת תוצאת משחק ועדכון דירוג נעשים בצורה עקבית.
- `RatingService` אינו מכיר WebSocket.

#### בדיקות

- ניצחון מול יריב חזק נותן יותר נקודות.
- הפסד מול יריב חזק מוריד פחות.
- דירוגי שני השחקנים מתעדכנים.
- ניסיון לעדכן אותו game_id שוב אינו משנה דירוג פעם נוספת.

#### תנאי סיום

משחק מלא מעדכן DB ומחזיר לשחקנים את הדירוגים החדשים.

---

## שלב E — Matchmaking, המתנה וניתוקים

### E.1 — Matchmaking

#### מטרה

לחבר שחקנים לפי טווח דירוג.

#### `Matchmaker`

מחזיק רשימת ממתינים:

```text
user_id
rating
connection_id
joined_at
```

#### כללים

- התאמה בטווח ±100 ELO.
- שחקן אינו מותאם לעצמו.
- לאחר התאמה שני השחקנים מוסרים מהתור באופן אטומי.
- נוצר Match חדש עם game_id חדש.
- אם לא נמצאה התאמה בתוך 60 שניות — מוחזרת הודעת timeout.
- ביטול Play מסיר את השחקן מהתור.

#### תכנון לעתיד

טווח ההתאמה וה־timeout יהיו ב־config, לא hard-coded בתוך האלגוריתם.

#### בדיקות

- התאמה בתוך הטווח.
- אין התאמה מחוץ לטווח.
- שני שחקנים אינם מותאמים פעמיים.
- timeout נבדק עם Clock מוזרק, בלי `sleep` אמיתי בטסט יחידה.

#### תנאי סיום

שני שחקנים שלוחצים Play מקבלים game_id וצבעים ומתחילים משחק עצמאי.

---

### E.2 — ניתוק, חיבור מחדש ו־Auto-resign

#### מטרה

לא לסיים משחק מיד בגלל ניתוק זמני.

#### התנהגות

```text
connection lost
    ↓
mark player disconnected
    ↓
start 20-second grace period
    ↓
reconnected? restore session and send full snapshot
    ↓ no
server applies resign
```

#### כללים

- Timer אחד לכל שחקן מנותק.
- חיבור מחדש מבטל את ה־Timer בצורה אטומית.
- Client מקבל grace period ומציג ספירה לאחור מקומית.
- השרת הוא שקובע אם הזמן הסתיים.
- לאחר חיבור מחדש נשלח Snapshot מלא, לא מסתמכים על כל האירועים שהוחמצו.

#### שינויים בליבה

`GameEngine.resign(color)` יתווסף רק אם זו הדרך הנקייה לייצג הפסד טכני. לחלופין, תוצאת הפסד טכני יכולה להישמר ברמת Match אם אינה חלק מחוקי המשחק עצמם.

#### בדיקות

- reconnect לפני 20 שניות אינו מסיים משחק.
- timeout מפעיל הפסד פעם אחת.
- reconnect לאחר סיום המשחק אינו מחייה אותו.
- spectator disconnected אינו גורם resign.

#### תנאי סיום

ניתוק קצר ניתן לשחזור; ניתוק ממושך מסיים משחק בצורה עקבית.

---

## שלב F — חדרים, צופים ולוגים

### F.1 — חדרים וצופים

#### מטרה

לאפשר יצירת Match פרטי והצטרפות לפי מזהה.

#### `RoomManager`

```text
room_id
match_id
white_player
black_player
spectators
status
```

#### Create

- יוצר room_id קצר וייחודי.
- היוצר משויך ל־White.
- מזהה החדר מוצג ב־UI.

#### Join

- המצטרף השני משויך ל־Black.
- כל מצטרף נוסף הוא Spectator.
- חדר לא קיים מחזיר שגיאה ברורה.

#### הרשאות

| Role | Snapshot | Events | Move/Jump |
|---|---:|---:|---:|
| White | כן | כן | כלים לבנים בלבד |
| Black | כן | כן | כלים שחורים בלבד |
| Spectator | כן | כן | לא |

#### תכנון UI

`room_dialog.py` ייפתח לפני חלון המשחק ויכלול:

- Text field.
- Create.
- Join.
- Cancel.

#### בדיקות

- Create יוצר מזהה ייחודי.
- המצטרף השני שחור.
- השלישי צופה.
- צופה אינו יכול לבצע פעולה.
- שידור מגיע לכל חברי החדר בלבד.

#### תנאי סיום

שני שחקנים וצופה רואים אותו משחק, ורק השחקנים מורשים לפעול.

---

### F.2 — לוגים בצד השרת והלקוח

#### מטרה

לאפשר איתור תקלות וניתוח פעילות בלי `print` מפוזר.

#### Server logs

- start/stop server.
- connection/disconnection.
- login/register result ללא סיסמאות.
- matchmaking join/match/timeout.
- room create/join/leave.
- game created/ended.
- invalid request.
- unexpected exception.

#### Client logs

- connection state.
- messages sent/received ברמת type בלבד כאשר payload רגיש.
- UI errors.
- reconnect attempts.

#### כללים

- משתמשים ב־`logging`.
- כל שורה משמעותית כוללת לפי הצורך `connection_id`, `user_id`, `game_id`, `room_id`.
- לא שומרים password או hash בלוג.
- אין להשתמש בלוג כתחליף למצב המשחק.

#### תנאי סיום

אפשר לעקוב מלוגים אחרי חיי משחק מלאים משני הצדדים.

---

# 9. פרוטוקול הודעות מוצע

## Envelope

```json
{
  "type": "move_request",
  "request_id": "optional-id",
  "game_id": "g_123",
  "payload": {}
}
```

בשלב הראשון `request_id` יכול להיות אופציונלי. הוא יתווסף כאשר נצטרך correlation או מניעת כפילויות.

## Client → Server

| type | payload |
|---|---|
| `ping` | `{}` |
| `identify` | `{ "username": "Noa" }` |
| `register` | `{ "username": "Noa", "password": "..." }` |
| `login` | `{ "username": "Noa", "password": "..." }` |
| `move_request` | `{ "from_row": 6, "from_col": 4, "to_row": 4, "to_col": 4 }` |
| `jump_request` | `{ "row": 6, "col": 4 }` |
| `play_request` | `{ "rated": true }` |
| `cancel_matchmaking` | `{}` |
| `create_room` | `{}` |
| `join_room` | `{ "room_id": "AB12CD" }` |

## Server → Client

| type | payload |
|---|---|
| `pong` | `{}` |
| `request_ok` | `{}` |
| `error` | `{ "code": "INVALID_MOVE", "message": "..." }` |
| `identity_assigned` | `{ "username": "Noa", "color": "w" }` |
| `state_snapshot` | board, pieces, game_over, winner, sequence |
| `game_event` | event kind and event data |
| `match_found` | game_id, color, opponent |
| `matchmaking_timeout` | `{}` |
| `player_disconnected` | color, grace_period_ms |
| `game_over` | winner, reason |
| `room_update` | room_id, players, spectators |

## Error codes

מומלץ להשתמש ב־Enums/קבועים:

```text
INVALID_MESSAGE
NOT_AUTHENTICATED
NOT_IN_GAME
NOT_YOUR_PIECE
INVALID_MOVE
GAME_OVER
SERVER_FULL
ROOM_NOT_FOUND
SPECTATOR_READ_ONLY
USERNAME_TAKEN
INVALID_CREDENTIALS
MATCHMAKING_TIMEOUT
```

---

# 10. Ownership של מצב

| מידע | בעלים |
|---|---|
| Board | GameEngine בתוך Match |
| Clock / movements | RealTimeArbiter בתוך אותו GameEngine |
| game_id | Match / GameRegistry |
| players and colors | Match |
| spectators | Match |
| WebSocket objects | GameServer / ClientSession manager |
| current Snapshot on client | ClientState |
| users and ratings | SQLite via repositories |
| matchmaking queue | Matchmaker |
| room membership | RoomManager |
| reconnect deadline | Match/connection coordination |

אין לשמור אותו State בשני מקומות ללא בעלים ברור.

---

# 11. Concurrency והגנה על Match

KFChess הוא משחק בזמן אמת ולכן קיימים כמה מקורות פעולה:

- פקודה משחקן לבן.
- פקודה משחקן שחור.
- לולאת Tick.
- disconnect/reconnect timer.

כל אלה עלולים לשנות אותו Match.

לכן לכל Match יהיה מנגנון סדרתי אחד:

```python
async with match.lock:
    # mutate engine/session state
```

או queue פנימי יחיד של פקודות. בשלב הראשון נבחר `asyncio.Lock` מפני שהוא פשוט וברור.

אין להשתמש ב־lock גלובלי לכל השרת, כדי שמשחק אחד לא יחסום משחק אחר.

---

# 12. אסטרטגיית Snapshots ואירועים

### Snapshot

מייצג את האמת המלאה הדרושה לציור:

- ממדי לוח.
- כל הכלים ומצביהם.
- selected state אם הוא UI-shared ונדרש.
- game over.
- winner.
- sequence.
- מידע HUD רלוונטי.

### Events

משמשים עבור:

- אנימציה מדויקת.
- צלילים.
- לוג מהלכים.
- ניקוד.
- הודעות התחלה וסיום.

### אסטרטגיה מאוזנת

- בחיבור ראשון או reconnect — Snapshot מלא.
- לאחר פעולות — Event ובמידת הצורך Snapshot חדש.
- בשלב הראשון אפשר לשדר Snapshot בכל שינוי, כדי לפשט.
- רק לאחר שהמערכת עובדת נשקול delta updates כדי לחסוך תעבורה.

---

# 13. אסטרטגיית בדיקות

## Unit tests

ללא WebSocket אמיתי כאשר אפשר:

- EventBus.
- Protocol encode/decode.
- Snapshot serialization.
- Match permissions.
- GameRegistry isolation.
- AuthService.
- Repositories עם SQLite in-memory.
- ELO.
- Matchmaker.
- RoomManager.
- Reconnect timeout logic עם Clock מוזרק.

## Integration tests

- Client ↔ Server ping/pong.
- Move roundtrip.
- שני Clients מקבלים אותו Snapshot.
- שני Matches אינם מדליפים עדכונים.
- login מול SQLite.
- reconnect roundtrip.

## End-to-End manual tests

בסוף כל שלב יוגדר תרחיש קצר שניתן להריץ ידנית.

### שער רגרסיה

לא עוברים לשלב הבא אם:

- הטסטים הקיימים של המשחק נשברו.
- מצב Local אינו עובד.
- קיימת תלות הפוכה אסורה.
- אין בדיקה בסיסית ליכולת החדשה.

---

# 14. כללי פיתוח לכל שלב

בכל שלב עובדים באותו סדר:

1. מגדירים את הדרישה המדויקת.
2. מגדירים מה מחוץ לתכולת השלב.
3. מציירים זרימת מידע קצרה.
4. בוחרים את מינימום הקבצים הנדרשים.
5. כותבים Unit tests ללוגיקה הטהורה.
6. מממשים גרסה מינימלית.
7. מריצים את כל הטסטים הקיימים.
8. מוסיפים Integration test אחד משמעותי.
9. מבצעים Refactor קטן בלבד.
10. מתעדים החלטות ו־TODOs אמיתיים.

---

# 15. מה לא נבנה מראש

כדי להימנע מ־Over-engineering, בשלב הראשון לא נוסיף:

- Microservices.
- Redis.
- PostgreSQL.
- כמה תהליכי Server.
- Message broker חיצוני.
- Abstract factory לכל שירות.
- Repository interface לכל אובייקט קטן.
- Event sourcing מלא.
- Replay של כל אירוע לצורך reconnect.
- Correlation IDs מורכבים לפני שיש צורך.
- Delta synchronization לפני ש־Snapshot מלא עובד.
- Generic plugin architecture.

נשאיר נקודות החלפה ברורות, אך לא נממש תשתית שאינה נדרשת.

---

# 16. הכנה להרחבות עתידיות

## ריבוי משחקים

מוכן דרך:

- `GameRegistry`.
- `Match` נפרד לכל משחק.
- lock ו־tick נפרדים.
- Broadcaster מוגבל ל־game_id.

## מעבר מ־SQLite למסד אחר

מוכן דרך:

- SQL מבודד ב־DAL.
- שירותי Auth/Rating אינם כותבים SQL.

## סוגי משחק נוספים

מוכן דרך:

- Factory קטן ליצירת Match/Engine רק כאשר באמת יידרש.
- Match אינו מניח תמיד לוח אחד גלובלי.

## הרחבת פרוטוקול

מוכנה דרך:

- `type` מרכזי.
- `payload` מובנה.
- parsing במקום אחד.
- version field יתווסף כאשר יהיו Clients בגרסאות שונות.

## שרת רב־תהליכי בעתיד

לא נתמך כעת, אבל הדרך אינה חסומה משום ש־Match הוא יחידת בידוד.

בעתיד יידרשו:

- ניתוב `game_id` ל־worker.
- מצב משותף ל־Matchmaking/Rooms.
- מסד נתונים שמתאים לכתיבה מקבילית.
- מנגנון Pub/Sub חיצוני.

אלו אינם חלק מדרישות הפרויקט הנוכחיות.

---

# 17. סיכונים מרכזיים והגנות

## סיכון: חוקי משחק זולגים לשרת

**הגנה:** כל Move/Jump עובר ל־GameEngine; השרת בודק רק זהות והרשאות.

## סיכון: זמן מתקדם רק כשלקוח שולח פקודה

**הגנה:** Tick loop אחד לכל Match.

## סיכון: שני משחקים מקבלים אירועים זה של זה

**הגנה:** Broadcaster ו־Subscriber per Match + בדיקת isolation.

## סיכון: Client משנה מצב מקומי לפני אישור

**הגנה:** ה־Client שולח request ומציג מצב authoritative מהשרת.

## סיכון: ELO מתעדכן פעמיים

**הגנה:** `UNIQUE(game_id, user_id)` ושירות idempotent.

## סיכון: ניתוק מסיים משחק פעמיים

**הגנה:** מצב Match ברור ו־timer cancellable תחת lock.

## סיכון: ארכיטקטורה גדולה מדי לפני שהרשת עובדת

**הגנה:** יצירת קבצים רק לפי השלב הנוכחי.

## סיכון: Refactor של הליבה שובר טסטים

**הגנה:** אין הזזת תיקיות קיימות ללא צורך תפקודי.

---

# 18. Roadmap קצר

```text
0. Core readiness
A. EventBus and game lifecycle events
B1. WebSocket ping/pong
B2. One client + one server-side Match
B3. Server tick loop
B4. Two clients + broadcast
B5. Existing UI connected as remote client
C. Username and color ownership
D1. SQLite DAL
D2. Authentication
D3. ELO and game persistence
E1. Matchmaking
E2. Disconnect and reconnect
F1. Rooms and spectators
F2. Logging and final stabilization
```

---

# 19. Definition of Done לכל שלב

שלב נחשב גמור רק כאשר:

- הדרישה עובדת מקצה לקצה.
- האחריות של המחלקות ברורה.
- אין תלות אסורה.
- קיימים טסטי יחידה ללוגיקה העיקרית.
- קיים תרחיש אינטגרציה או E2E.
- כל הטסטים הישנים עוברים.
- מצב Local עדיין עובד.
- שגיאות מוחזרות בצורה צפויה.
- אין `print` debugging שנשאר בקוד.
- תועדו החלטות או מגבלות חשובות.

---

# 20. ממצאי סקירת הליבה (שלב 0 — הושלם)

| שאלה | ממצא |
|---|---|
| API ציבורי של `GameEngine` | `select`, `clear_selection`, `get_selected`, `move_request(target)`, `jump(position)`, `tick(ms)`, `create_snapshot()`, `get_board()`, `is_game_over()`, `set_game_over()`. יתווספו: `move_from_to`, `start_game`, `get_winner`, EventBus publish/subscribe, ובהמשך `resign`. |
| `GameSnapshot` | ב־[`snapshots/`](snapshots/) — headless, ניתן לייבוא בשרת בלי View. |
| אירועים קיימים | אין EventBus. ה־arbiter צובר מחרוזות `"GAME_OVER"` ב־`get_events()`. |
| מי מקדם זמן | `GameRunner` קורא ל־`engine.tick(TICK_MS)` בכל פריים; `Controller.wait` הוא alias ל־`tick`. |
| פתיחת לוח | `BoardParser.parse` ב־`main.create_game()` / `board_io/`. |
| Local wiring | `main.py` → `GameEngine` + `Controller` + `view.factory.create_ui` → `GameRunner`. אין `DisplayManager`. |
| טסטים | `tests/unit/test_game_engine.py` ועוד; HUD קורא ניקוד/לוג מתוך Snapshot, לא מ־Observer. |

החלטות שתועדו בעקבות הסקירה: סעיפים 5.7 (`move_from_to`) ו־5.8 (`selected_cell` ברשת).

---

## סיכום החלטה

נבנה מערכת פשוטה אך לא קצרת־ראייה:

- הליבה נשארת נקייה.
- השרת מחזיק את האמת.
- כל משחק מבודד בתוך Match.
- הפרוטוקול מרוכז.
- SQLite מבודד ב־DAL.
- ה־Client מציג Snapshot ולא מפעיל חוקי משחק.
- כל דרישה נבנית כשלב עצמאי, נבדקת ורק אז מורחבת.

כך נוכל לעמוד בדרישות ההגשה בלי ליצור מערכת מסובכת מדי, ובמקביל להשאיר דרך ברורה למשחקים מקבילים, חדרים, צופים ותשתית גדולה יותר בעתיד.
