# AI_PROMPT_LEDGER.md

**Student ID:** 20231000031

**Course:** Advanced Object-Oriented Programming & Systems Design

---

# BUG 1 – Buffer Leak (Encapsulation Flaw)

## AI Prompt

> Analyze the TelemetryBuffer class and identify any encapsulation problems caused by mutable default arguments. Suggest a Pythonic solution that prevents shared memory between object instances.

## Initial AI Suggestion

The AI suggested replacing the default list parameter with `None` and creating a new list inside the constructor.

## Why the Initial Suggestion Was Not Enough

The AI explained the Python issue but did not relate it to the avionics telemetry system. In this project, multiple peripherals run simultaneously, and sharing the same buffer could mix telemetry packets from different sensors, producing incorrect diagnostic results.

## Final Engineering Justification

The constructor was changed from:

```python
frame_buffer=[]
```

to

```python
frame_buffer=None
```

and initialized with

```python
self.frame_buffer = [] if frame_buffer is None else frame_buffer
```

This ensures every telemetry buffer owns its own memory and prevents unintended data sharing between hardware peripherals.

---

# BUG 2 – Polymorphic Trap (Liskov Substitution Principle)

## AI Prompt

> Review the IMUPeripheral class and verify that poll_raw_voltage() follows the contract of the base class. If necessary, modify it so that polymorphism is preserved.

## Initial AI Suggestion

The AI identified that the method sometimes returned a dictionary instead of a floating-point voltage.

## Why the Initial Suggestion Was Not Enough

The explanation focused only on Python inheritance. It did not explain that the bus controller performs voltage normalization using arithmetic operations. Returning a dictionary would cause runtime errors during signal processing.

## Final Engineering Justification

The method was modified so that it always returns a floating-point voltage value. Fault conditions are recorded in the telemetry buffer instead of changing the return type.

This preserves the Liskov Substitution Principle because every peripheral now behaves consistently with the base class interface.

---

# BUG 3 – Race Condition (Concurrency)

## AI Prompt

> Inspect the multithreaded avionics bus controller for race conditions. Recommend a thread-safe solution that protects the shared telemetry register.

## Initial AI Suggestion

The AI recommended using `threading.Lock()` to synchronize writes to the shared register.

## Why the Initial Suggestion Was Not Enough

The AI initially suggested locking only individual assignment statements. That still allowed multiple threads to read the shared data simultaneously before writing updates.

## Final Engineering Justification

A mutex lock was added to the `AvionicsBusMaster` class.

```python
self.lock = threading.Lock()
```

The complete read-modify-write sequence was enclosed inside

```python
with self.lock:
```

This guarantees that only one thread updates the shared telemetry register at a time, preventing inconsistent register values and packet counts.

---

# Reflection

Artificial intelligence helped identify common programming issues quickly, but every suggestion still required verification against the project requirements. Understanding object-oriented programming, encapsulation, polymorphism, and multithreading was necessary to implement the correct solution. AI served as a debugging assistant, while the final engineering decisions were based on software engineering principles and the system requirements.