import pygame
import sys


class Game(object):
    """
    The Game class represents the main game logic and control.

    It initializes the game window, manages game settings, handles 
    player and fruit interactions, generates the maze layout, and 
    controls the game loop and rendering process.
    """
    
    def __init__(self):
        """
        Initialize the Game class.
        
        This method sets up Pygame, initializes game variables
        and title, loads settings from a JSON file, and prepares
        the player and game objects for the game.
        """
        pygame.init()
        self.screen_width: int = 600
        self.screen_height: int = 600
        self.cell_size: int = 25
        self.panel_size: int = 300
        self.screen = pygame.display.set_mode((self.screen_width + self.panel_size, 
                                               self.screen_height - self.cell_size))
        pygame.display.set_caption('Maze (game)')

        self.file_game_settings: str = 'settings.json'

        from json.decoder import JSONDecodeError
        from json import load
        
        # Load game settings from a JSON file
        try:
            with open(self.file_game_settings, 'r', encoding='UTF-8') as file:
                self.settings: dict = load(file)
        except (FileNotFoundError, JSONDecodeError):
            # Default settings if the file is not found or corrupted
            self.settings: dict = {
                'most more best score': 0,
                'most more completed level': 0,
                'last best score': 0,
                'last completed level': 0,
            }

        # Game state variables
        self.fps: int = 60
        self.running = True
        self.next_number_fruits: int = 3
        self.is_completed_level = False
        self.clock = pygame.time.Clock()

        # Score tracking variables
        self.most_more_best_score = self.settings['most more best score']
        self.most_more_completed_level = self.settings['most more completed level']
        self.last_best_score = self.settings['last best score']
        self.last_completed_level = self.settings['last completed level']
        self.score: int = 0
        self.best_score: int = 0
        self.completed_level: int = 0
        self.images_fruits: tuple = [
            'apple', 'avocado', 'banana', 'cherry', 
            'coconut','grapes','pear', 'pineapple', 
            'strawberry', 'watermelon'
        ]

        # Font settings for rendering text
        self.font = pygame.font.Font(None, 25)
        self.font_for_win = pygame.font.SysFont('comicsansms', 60)

        # Sprite groups for managing game objects
        self.sprites = pygame.sprite.Group()
        self.player_obstacles = pygame.sprite.Group()
        self.player = Player(self.cell_size + self.cell_size // 2, self.cell_size + self.cell_size // 2,
                             self.screen_width, self.screen_height, self.fps, self.cell_size)
        self.sprites.add(self.player)
        self.fruits = pygame.sprite.Group()
        self.generate_maze()


    def generate_maze(self):
        """
        Generate the maze layout and place fruits in it.

        This method creates a maze using a depth-first search algorithm,
        then randomly places fruits in valid positions within the maze.
        It also creates obstacles based on the maze structure.
        """
        random = __import__('random', fromlist=('shuffle', 'choice', 'randint'))

        # Determine maze dimensions
        cols = (self.screen_width // self.cell_size) - 1
        rows = (self.screen_height // self.cell_size) - 1
        maze = [[1 for _ in range(cols)] for _ in range(rows)]
        stack = [(1, 1)]
        maze[1][1] = 0

        # Function to carve passages in the maze
        def carve_passages():
            while stack:
                cx, cy = stack[-1]
                directions = [(2, 0), (-2, 0), (0, 2), (0, -2)]
                random.shuffle(directions)
                carved = False
                for direction in directions:
                    nx, ny = cx + direction[0], cy + direction[1]
                    if 0 <= nx < cols and 0 <= ny < rows and maze[ny][nx] == 1:
                        maze[ny][nx] = 0
                        maze[cy + direction[1] // 2][cx + direction[0] // 2] = 0
                        stack.append((nx, ny))
                        carved = True
                        break
                if not carved:
                    stack.pop()

        carve_passages()

        # Generate fruit positions in the maze
        number_fruit = self.next_number_fruits
        while number_fruit != 0:
            fruit_pos = random.choice(['top', 'bottom'])
            if fruit_pos == 'top':
                x = random.randint(1, rows - 1)
                y = random.randint(8, cols - 1)
            else:
                x = random.randint(8, rows - 1)
                y = random.randint(1, cols - 1)

            # Check if the position is valid
            if maze[y][x] == 0:
                x_pos = x * self.cell_size
                y_pos = y * self.cell_size
                image = random.choice(self.images_fruits)
                fruit = GameFruit(image, x_pos + self.cell_size // 4, y_pos + self.cell_size // 5, 
                                  self.cell_size - self.cell_size // 2.5, 
                                  random.randint(0, 30), self.fps // 2)
                self.fruits.add(fruit)
                self.sprites.add(fruit)
                number_fruit -= 1

        # Create obstacles based on the maze structure
        for y in range(rows):
            for x in range(cols):
                if maze[y][x] == 1:
                    x_pos = x * self.cell_size
                    y_pos = y * self.cell_size
                    obstacle = Wall(x_pos, y_pos, self.cell_size, self.cell_size, (0, 180, 0))
                    self.sprites.add(obstacle)
                    self.player_obstacles.add(obstacle)


    def run_game(self):
        """
        Start the main game loop.

        This method handles events, updates the game state, 
        draws the current frame, and manages the game running state.
        It also saves game settings before exiting.
        """
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if self.is_completed_level:
                        self.restart_game()

            self.draw_game()
            self.update()

        # Save game settings before exiting
        from json import dump
        self.settings['most more best score'] = max(self.most_more_best_score, self.settings['most more best score'])
        self.settings['most more completed level'] = max(self.most_more_completed_level, self.settings['most more completed level'])

        if self.best_score != 0 and self.completed_level != 0:
            self.settings['last best score'] = self.best_score
            self.settings['last completed level'] = self.completed_level

        with open(self.file_game_settings, 'w', encoding='UTF-8') as file:
            dump(self.settings, file)

        pygame.quit()
        sys.exit()


    def draw_game(self):
        """
        Render the current game state on the screen.

        This method draws all game objects, the score panel, and
        displays win messages if the level is completed.
        """
        self.screen.fill((0, 255, 0))
        self.sprites.draw(self.screen)
        pygame.draw.rect(self.screen, (0, 180, 0), (self.screen_width - self.cell_size, 0, 
                                                    self.panel_size + self.cell_size, 
                                                    self.screen_height - self.cell_size))

        # Render best results
        best_results_text = self.font.render('The Best Results'.title(), True, (250, 250, 250))
        most_more_best_score_text = self.font.render(f'Most More Best Score: {self.most_more_best_score}'.title(), True, (250, 250, 250))
        most_more_completed_level_text = self.font.render(f'Most More Completed Levels: {self.most_more_completed_level}'.title(), True, (250, 250, 250))

        # Render last results
        last_best_results_text = self.font.render('Last Results'.title(), True, (250, 250, 250))
        last_best_score_text = self.font.render(f'Last Best Score: {self.last_best_score}'.title(), True, (250, 250, 250))
        last_completed_level_text = self.font.render(f'Last Completed Levels: {self.last_completed_level}'.title(), True, (250, 250, 250))

        # Render current results
        current_now_best_results_text = self.font.render('Current Now Results'.title(), True, (250, 250, 250))
        current_now_score_text = self.font.render(f'Score: {self.score}'.title(), True, (250, 250, 250))
        current_now_best_score_text = self.font.render(f'Best Score: {self.best_score}'.title(), True, (250, 250, 250))
        current_now_completed_level_text = self.font.render(f'Completed Levels: {self.completed_level}'.title(), True, (250, 250, 250))

        # Blit the rendered text onto the screen
        self.screen.blit(best_results_text, (self.screen_width + 60, 10))
        self.screen.blit(most_more_completed_level_text, (self.screen_width, 10 + self.cell_size))
        self.screen.blit(most_more_best_score_text, (self.screen_width + 30, 10 + self.cell_size * 2))
        self.screen.blit(last_best_results_text, (self.screen_width + 60, 10 + self.cell_size * 4))
        self.screen.blit(last_completed_level_text, (self.screen_width + 60, 10 + self.cell_size * 5))
        self.screen.blit(last_best_score_text, (self.screen_width + 30, 10 + self.cell_size * 6))

        self.screen.blit(current_now_best_results_text, (self.screen_width + 60, 10 + self.cell_size * 8))
        self.screen.blit(current_now_score_text, (self.screen_width + 30, 10 + self.cell_size * 9))
        self.screen.blit(current_now_best_score_text, (self.screen_width + 30, 10 + self.cell_size * 10))
        self.screen.blit(current_now_completed_level_text, (self.screen_width + 30, 10 + self.cell_size * 11))

        # Display win message if the level is completed
        if self.is_completed_level:
            pygame.draw.rect(self.screen, (0, 0, 255), (self.cell_size, self.cell_size, 
                                                        self.screen_width - self.cell_size * 3,
                                                        self.screen_height - self.cell_size * 3))
            winner_text = self.font_for_win.render('You Win'.lower(), True, (250, 250, 250))
            self.screen.blit(winner_text, (self.screen_width // 2 - self.cell_size * 5, 
                                           self.screen_height // 2 - self.cell_size * 3))

    def update(self):
        """
        Update the game state.

        This method handles player movements, checks for collisions with
        obstacles and fruits, updates the score, and controls the frame rate.
        """
        # Update player movements and check collisions
        self.player.player_moves()

        for obstacle_player in pygame.sprite.spritecollide(self.player, self.player_obstacles, False):
            # Handle collisions with obstacles
            if self.player.is_move_y:
                if self.player.rect.right < obstacle_player.rect.centerx:
                    self.player.rect.right = obstacle_player.rect.left
                elif self.player.rect.left > obstacle_player.rect.centerx:
                    self.player.rect.left = obstacle_player.rect.right
                elif self.player.rect.top > obstacle_player.rect.centery:
                    self.player.rect.top = obstacle_player.rect.bottom
                elif self.player.rect.bottom < obstacle_player.rect.centery:
                    self.player.rect.bottom = obstacle_player.rect.top
            else:
                if self.player.rect.top > obstacle_player.rect.centery:
                    self.player.rect.top = obstacle_player.rect.bottom
                elif self.player.rect.bottom < obstacle_player.rect.centery:
                    self.player.rect.bottom = obstacle_player.rect.top
                elif self.player.rect.right < obstacle_player.rect.centerx:
                    self.player.rect.right = obstacle_player.rect.left
                elif self.player.rect.left > obstacle_player.rect.centerx:
                    self.player.rect.left = obstacle_player.rect.right

        # Check for collisions with fruits
        for _ in pygame.sprite.spritecollide(self.player, self.fruits, True):
            self.score += 1
            if self.score > self.best_score:
                self.best_score = self.score
                if self.best_score > self.most_more_best_score:
                    self.most_more_best_score = self.best_score

        # Animate fruits
        for fruit in self.fruits:
            fruit.animation()

        # Check if level is completed
        if not self.fruits.sprites():
            self.is_completed_level = True

        # Control the frame rate
        self.clock.tick(self.fps)
        pygame.display.update()


    def restart_game(self):
        """
        Restart the game.

        This method resets the game state, including score, completion status,
        and player position. It also generates a new maze and starts the game loop.
        """
        # Reset game state for restarting
        self.score = 0
        self.is_completed_level = False
        self.player.rect.topleft = (self.cell_size + self.cell_size // 2, self.cell_size + self.cell_size // 2)
        self.next_number_fruits += 1
        self.sprites.empty()
        self.player_obstacles.empty()
        self.generate_maze()
        self.player = Player(self.cell_size + self.cell_size // 2, self.cell_size + self.cell_size // 2,
                             self.screen_width, self.screen_height, self.fps, self.cell_size)
        self.sprites.add(self.player)
        self.completed_level += 1
        self.run_game()


class Wall(pygame.sprite.Sprite):
    """
    The Wall class represents a wall or obstacle in the game.

    It serves as a specific type of game object that blocks the player's movement.
    """
    
    def __init__(self, x, y, width, height, color):
        """
        Initialize a wall object.

        This method creates a wall with the specified dimensions and color.
        """
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))


class GameFruit(pygame.sprite.Sprite):
    """
    The GameFruit class represents a fruit object in the game.

    It extends the Sprite class to include properties for animation,
    such as vertical movement to create a bouncing effect.
    """
    
    def __init__(self, image, x, y, cell_size, animation_wait, fps):
        """
        Initialize a fruit object.

        This method creates a fruit with specified image, position,
        size, animation delay, and frames per second for animation behavior.
        """
        super().__init__()
        self.image = pygame.image.load(f'assets/Graphics/fruits/{image}.png')

        self.image = pygame.transform.scale(
            self.image,
            (cell_size, cell_size)
        )

        self.rect = self.image.get_rect(topleft=(x, y))

        self.animation_wait = animation_wait
        self.animation_state = True
        self.fps = fps
        self.speed: int = 5


    def animation(self):
        """
        Animate the fruit's vertical movement.

        This method changes the position of the fruit to create an
        up-and-down bouncing effect based on the animation state.
        """
        if self.animation_wait >= self.fps:
            self.animation_wait = 0
            if self.animation_state:
                self.rect.y += self.speed
            else:
                self.rect.y -= self.speed
            self.animation_state = not self.animation_state
        else:
            self.animation_wait += 1


class Player(pygame.sprite.Sprite):
    """
    The Player class represents the main character controlled by the player.

    It handles player input for movement, manages player animation,
    and keeps track of the player's position within the game world.
    """
    
    def __init__(self, x, y, screen_width, screen_height, fps, cell_size, speed=5):
        """
        Initialize the player character.

        This method sets up the player's images for animation, initializes
        properties for movement and screen boundaries, and prepares for
        handling player input.
        """
        super().__init__()
        # Load and scale player images for animation
        self.images = [
            pygame.transform.scale(
            pygame.image.load(f'assets/Graphics/player_animation/player_image_{i}.png'), 
            (cell_size, cell_size)) for i in range(4)
        ]

        for image in self.images: image.set_colorkey((255, 255, 255))

        self.image = self.images[0]
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.fps = fps
        self.wait: int = 0
        self.index_image: int = 0
        self.is_move_y = bool


    def animation(self):
        """
        Handle player image animation.

        This method updates the player's displayed image based on the frame
        count, creating a smooth animation effect as the player moves.
        """
        if self.wait == self.fps // 2:
            self.wait = 0
            self.index_image = (self.index_image + 1) % len(self.images)
            self.image = self.images[self.index_image]
        else:
            self.wait += 1


    def player_moves(self):
        """
        Handle player movement based on keyboard input.

        This method checks for keyboard events to move the player
        character in the specified direction and manages the animation state.
        """
        self.animation()
        key = pygame.key.get_pressed()
        if key[pygame.K_RIGHT] and self.rect.right < self.screen_width:
            self.rect.x += self.speed
            self.is_move_y = False
        elif key[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
            self.is_move_y = False
        elif key[pygame.K_UP] and self.rect.top > 0:
            self.rect.y -= self.speed
            self.is_move_y = True
        elif key[pygame.K_DOWN] and self.rect.bottom < self.screen_height:
            self.rect.y += self.speed
            self.is_move_y = True


if __name__ == '__main__':
    Game().run_game()
