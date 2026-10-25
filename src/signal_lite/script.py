from .turn import Turn

def text_to_lines(text: str) -> list[str]:
    lines = text.split("\n")
    filtered_lines = []

    for line in lines:
        line = line.strip()
        if line == "":
            continue
        filtered_lines.append(line)

    return filtered_lines

def text_to_turns(text: str) -> list[Turn]:
    lines = text_to_lines(text)
    turns: list[Turn] = []

    for turn_id, line in enumerate(lines, start=1):
        turn = line_to_turn(line, turn_id)
        turns.append(turn)

    return turns

def line_to_turn(line: str, turn_id: int) -> Turn:
    speaker, text = line.split(":", 1)
    turn = Turn(turn_id=turn_id, speaker=speaker.strip().lower(), text=text.strip())
    return turn
