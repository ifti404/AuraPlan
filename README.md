# AuraPlan

**An offline, context-aware academic productivity assistant.**

AuraPlan helps students organize academic work and decide what to focus on next. It is designed around task deadlines, estimated effort, and the student's current energy level, with local storage and offline-first operation.

> **Project status:** Student project in development. Features and setup instructions may change as implementation progresses.

## The idea

Most task lists help you record what needs to be done. AuraPlan aims to help answer: **“Given my tasks, deadlines, and energy right now, what should I work on next?”**

For example, when energy is low, it could recommend a lighter reading or note-organizing task. When energy is high, it could prioritize a demanding assignment that is approaching its deadline.

## Planned features

- Create, view, edit, complete, and delete academic tasks
- Record subjects, due dates, priorities, and estimated durations
- Recommend tasks using local rules that consider deadlines, task load, and energy level
- Store task data locally in SQLite
- Explore optional offline voice commands for quick task entry
- Explore optional focus-session presence tracking

Voice input and focus tracking are optional planned components; availability will depend on the current release and supported hardware.

## Planned technology

- **Language:** Python
- **Desktop interface:** Tkinter or CustomTkinter
- **Database:** SQLite
- **Scheduling and classification:** Lightweight, local rule-based logic
- **Possible optional components:** Vosk for offline speech recognition; OpenCV for focus-session presence detection

AuraPlan is intended to work without cloud AI or an internet connection for its core task-management and recommendation features.

## Getting started

The application is under development, so installation steps will be added when the repository has a runnable release. The planned baseline is a Python desktop application using SQLite for local data storage.

When setup is available, this section should include the supported Python version, dependency installation command, and launch command.

## How recommendations are intended to work

AuraPlan's planned recommendation logic uses information such as:

1. **Deadline urgency** — tasks due sooner receive more attention.
2. **Task load** — tasks are grouped or scored by estimated mental effort.
3. **Current energy** — recommendations favor tasks that fit the student's reported energy level.

Recommendations are decision support. Students remain in control of their schedule and can choose any task.

## Privacy

The project is designed to keep core academic task data on the user's device in a local SQLite database. Optional microphone or camera features should only run when enabled by the user and during the relevant activity. See the implementation and release notes for the behavior of each version.

## Contributing

This is a student project. Contributions, suggestions, and bug reports are welcome. Please open an issue to discuss a substantial change before starting work.

## License

No license has been selected yet. Until one is added to this repository, all rights are reserved by the project authors.

## Authors
