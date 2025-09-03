from time import time


class GestureController:
    def __init__(self, music_player, cooldown=2.0):
        self.music_player = music_player
        self.last_action = None
        self.last_time = 0
        self.cooldown = cooldown

    def handle_gesture(self, gesture):
        now = time()

        if gesture == "Next":
            if self._can_trigger("Next", now):
                self.music_player.next()
                self._update_state("Next", now)

        elif gesture == "Previous":
            if self._can_trigger("Previous", now):
                self.music_player.prev()
                self._update_state("Previous", now)

        elif gesture == "Play":
            if self._can_trigger("Play", now):
                self.music_player.play()
                self._update_state("Play", now)

        elif gesture == "Pause":
            if self._can_trigger("Pause", now):
                self.music_player.stop()
                self._update_state("Pause", now)

    def _can_trigger(self, action, now):
        return (action != self.last_action) or (now - self.last_time > self.cooldown)

    def _update_state(self, action, now):
        self.last_action = action
        self.last_time = now
