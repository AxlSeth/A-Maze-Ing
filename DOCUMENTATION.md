# A-Maze-ing — Documentation complète

---

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Constantes globales](#constantes-globales)
3. [Classe Maze_Generator](#classe-maze_generator)
4. [Classe MazeDisplay](#classe-mazedisplay)
5. [Fonction load_config](#fonction-load_config)
6. [Point d'entrée principal](#point-dentrée-principal)
7. [Format du fichier de configuration](#format-du-fichier-de-configuration)
8. [Format du fichier de sortie](#format-du-fichier-de-sortie)
9. [Encodage des murs (bits)](#encodage-des-murs-bits)
10. [Touches clavier MLX](#touches-clavier-mlx)

---

## Vue d'ensemble

Le projet A-Maze-ing est un générateur de labyrinthe en Python utilisant :

- L'algorithme **Recursive Backtracker (DFS)** pour la génération
- L'algorithme **BFS (Breadth-First Search)** pour la résolution
- La bibliothèque **MLX** pour l'affichage graphique

```
config.txt
    ↓
load_config()
    ↓
Maze_Generator.generate()
    ↓
Maze_Generator.solve()
    ↓
MazeDisplay.run()  →  fenêtre graphique MLX
```

---

## Constantes globales

```python
CELL_SIZE      = 20    # taille d'une cellule en pixels
WALL_THICKNESS = 3     # épaisseur des murs en pixels

COLOR_WALL     = 0xFFFFFFFF  # blanc  — murs
COLOR_BG       = 0xFF000000  # noir   — fond
COLOR_ENTRY    = 0xFF00FF00  # vert   — entrée
COLOR_EXIT     = 0xFFFF0000  # rouge  — sortie
COLOR_PATH     = 0xFF00FFFF  # cyan   — chemin solution
```

> Les couleurs sont au format `0xAARRGGBB` (Alpha, Rouge, Vert, Bleu).
> Le canal Alpha `0xFF` signifie opaque.

---

## Classe Maze_Generator

Responsable de la **génération** et de la **résolution** du labyrinthe.
Ne contient aucune logique d'affichage.

### `__init__(width, height)`

Initialise la grille du labyrinthe.

| Paramètre | Type  | Description                        |
|-----------|-------|------------------------------------|
| `width`   | `int` | Nombre de cellules en largeur      |
| `height`  | `int` | Nombre de cellules en hauteur      |

```python
mg = Maze_Generator(20, 15)
# mg.maze → tableau 2D de 15 lignes × 20 colonnes
# chaque cellule initialisée à 0xF (tous les murs fermés)
```

---

### `set_borders()`

Ferme tous les murs sur les **bords extérieurs** du labyrinthe.

- Ligne 0          → ajoute le mur Nord  (bit 0 = 1)
- Ligne height-1   → ajoute le mur Sud   (bit 2 = 4)
- Colonne 0        → ajoute le mur Ouest (bit 3 = 8)
- Colonne width-1  → ajoute le mur Est   (bit 1 = 2)

```python
mg.set_borders()
# Appelé automatiquement à la fin de generate()
```

---

### `generate(seed=None)`

Génère le labyrinthe avec l'algorithme **Recursive Backtracker**.

| Paramètre | Type         | Description                                       |
|-----------|--------------|---------------------------------------------------|
| `seed`    | `int | None` | Graine aléatoire. `None` = aléatoire à chaque fois |

**Fonctionnement :**

1. Initialise toutes les cellules à `0xF` (4 murs fermés)
2. Démarre la fonction `carve()` depuis la cellule `(0, 0)`
3. `carve()` choisit un voisin non visité au hasard
4. Casse le mur entre la cellule actuelle et le voisin
5. Se déplace vers le voisin et recommence
6. Si aucun voisin disponible → **backtrack** (retour à la cellule précédente)
7. Appelle `set_borders()` pour fermer les bords extérieurs

```python
mg.generate(seed=42)   # reproductible
mg.generate()          # aléatoire
```

**Casser un mur entre deux cellules :**

```
Aller vers l'Est :
  cellule actuelle  → enlève bit Est   (& ~2)
  cellule voisine   → enlève bit Ouest (& ~8)
Les deux côtés doivent être mis à jour ensemble.
```

---

### `solve(entry, exit_point) → list`

Trouve le **chemin le plus court** entre l'entrée et la sortie avec BFS.

| Paramètre    | Type    | Description                         |
|--------------|---------|-------------------------------------|
| `entry`      | `tuple` | Coordonnées d'entrée `(row, col)`   |
| `exit_point` | `tuple` | Coordonnées de sortie `(row, col)`  |

**Retourne :** liste de directions `['N', 'S', 'E', 'W', ...]`

**Retourne `[]`** si aucun chemin n'existe.

```python
path = mg.solve((0, 0), (14, 19))
# exemple : ['S', 'S', 'E', 'E', 'N', 'E', ...]
```

**Fonctionnement BFS :**

```
file = [(row_départ, col_départ, [])]
tant que file non vide :
    prendre la première cellule
    si c'est la sortie → retourner le chemin
    pour chaque direction (N, S, E, W) :
        si le mur est OUVERT (bit = 0) et cellule non visitée :
            ajouter à la file avec le chemin mis à jour
```

---

## Classe MazeDisplay

Responsable de l'**affichage graphique** avec MLX.

### `__init__(mg, entry, exit_point)`

Initialise MLX, crée la fenêtre et le buffer image.

| Paramètre    | Type             | Description                          |
|--------------|------------------|--------------------------------------|
| `mg`         | `Maze_Generator` | Instance du générateur de labyrinthe |
| `entry`      | `tuple`          | Coordonnées d'entrée `(row, col)`    |
| `exit_point` | `tuple`          | Coordonnées de sortie `(row, col)`   |

**Ce qui est créé :**

```
win_w = mg.width  × CELL_SIZE + WALL_THICKNESS
win_h = mg.height × CELL_SIZE + WALL_THICKNESS + 30  (30px pour le menu)

mlx_ptr  → connexion MLX
win_ptr  → fenêtre graphique
img      → buffer image (dessin rapide en mémoire)
addr     → accès direct aux pixels du buffer
```

---

### `put_pixel(x, y, color)`

Écrit un pixel dans le **buffer image** (en mémoire, pas encore affiché).

| Paramètre | Type  | Description           |
|-----------|-------|-----------------------|
| `x`       | `int` | Position horizontale  |
| `y`       | `int` | Position verticale    |
| `color`   | `int` | Couleur `0xAARRGGBB`  |

```python
# Formule d'offset dans le buffer
offset = y * line_len + x * (bpp // 8)
addr[offset:offset+4] = color.to_bytes(4, 'little')
```

---

### `draw_rect(x, y, w, h, color)`

Dessine un **rectangle plein** en appelant `put_pixel` pour chaque pixel.

| Paramètre | Type  | Description                   |
|-----------|-------|-------------------------------|
| `x`       | `int` | Coin haut-gauche (horizontal) |
| `y`       | `int` | Coin haut-gauche (vertical)   |
| `w`       | `int` | Largeur en pixels             |
| `h`       | `int` | Hauteur en pixels             |
| `color`   | `int` | Couleur `0xAARRGGBB`          |

---

### `draw_cell(row, col, cell_value)`

Dessine une **cellule** avec ses murs selon la valeur hexadécimale.

| Paramètre    | Type  | Description                   |
|--------------|-------|-------------------------------|
| `row`        | `int` | Ligne dans la grille          |
| `col`        | `int` | Colonne dans la grille        |
| `cell_value` | `int` | Valeur hex encodant les murs  |

**Structure d'une cellule en pixels :**

```
px = col × CELL_SIZE
py = row × CELL_SIZE

┌──────────────────────┐  ← mur Nord  : draw_rect(px, py,       C, T)
│░░░░░░░░░░░░░░░░░░░░░░│
│░░    intérieur    ░░░│  ← mur Ouest : draw_rect(px, py,       T, C)
│░░                 ░░░│  ← mur Est   : draw_rect(px+C-T, py,   T, C)
│░░░░░░░░░░░░░░░░░░░░░░│
└──────────────────────┘  ← mur Sud   : draw_rect(px, py+C-T,  C, T)

C = CELL_SIZE, T = WALL_THICKNESS
```

---

### `draw_maze()`

Dessine **l'intégralité du labyrinthe** dans le buffer, puis l'affiche.

**Ordre des opérations :**

```
1. Effacer le buffer (remplir de noir)
2. Dessiner toutes les cellules (draw_cell)
3. Marquer l'entrée en vert (mark_special)
4. Marquer la sortie en rouge (mark_special)
5. Dessiner le chemin si activé (draw_path)
6. Envoyer le buffer vers la fenêtre (mlx_put_image_to_window)
7. Afficher le menu texte (mlx_string_put)
```

> `mlx_put_image_to_window` envoie tout le buffer en **une seule requête**,
> ce qui est beaucoup plus rapide que d'appeler `mlx_pixel_put` pixel par pixel.

---

### `mark_special(row, col, color)`

Colorie le **centre d'une cellule** avec une couleur donnée.
Utilisé pour marquer l'entrée (vert) et la sortie (rouge).

| Paramètre | Type  | Description              |
|-----------|-------|--------------------------|
| `row`     | `int` | Ligne dans la grille     |
| `col`     | `int` | Colonne dans la grille   |
| `color`   | `int` | Couleur `0xAARRGGBB`     |

```python
# Position du carré intérieur
px   = col × CELL_SIZE + WALL_THICKNESS + 1
py   = row × CELL_SIZE + WALL_THICKNESS + 1
size = CELL_SIZE - 2 × WALL_THICKNESS - 2
```

---

### `draw_path()`

Colorie en cyan toutes les cellules du **chemin solution**.

Utilise `self.path` (liste de directions) et `self.entry` comme point de départ.
Parcourt les directions une par une en mettant à jour `(row, col)` à chaque étape.

```python
moves = {'N':(-1,0), 'S':(1,0), 'E':(0,1), 'W':(0,-1)}
# Pour chaque direction : colorier la cellule, puis avancer
```

---

### `run()`

Lance la **boucle principale MLX** et branche les événements.

**Hooks enregistrés :**

| Hook            | Événement        | Action                      |
|-----------------|------------------|-----------------------------|
| `mlx_loop_hook` | Chaque frame     | Redessine le labyrinthe     |
| `mlx_key_hook`  | Touche relâchée  | Gère les actions clavier    |
| `mlx_hook(33)`  | Clic sur bouton ✕ | Ferme proprement la fenêtre |

**Touches disponibles :**

| Touche   | Keycode | Action                             |
|----------|---------|------------------------------------|
| `1`      | 49      | Régénère un nouveau labyrinthe     |
| `2`      | 50      | Affiche / cache le chemin solution |
| `Escape` | 65307   | Quitte le programme                |

**Nettoyage après la boucle (ordre obligatoire) :**

```python
mlx.mlx_destroy_image(mlx_ptr, img)       # 1. image d'abord
mlx.mlx_destroy_window(mlx_ptr, win_ptr)  # 2. fenêtre ensuite
mlx.mlx_release(mlx_ptr)                  # 3. connexion MLX en dernier
```

---

## Fonction load_config

### `load_config(filename) → dict`

Lit et parse le fichier de configuration.

| Paramètre  | Type  | Description                   |
|------------|-------|-------------------------------|
| `filename` | `str` | Chemin vers le fichier `.txt` |

**Retourne :** dictionnaire avec les clés suivantes :

| Clé           | Type    | Exemple        |
|---------------|---------|----------------|
| `WIDTH`       | `int`   | `20`           |
| `HEIGHT`      | `int`   | `15`           |
| `ENTRY`       | `tuple` | `(0, 0)`       |
| `EXIT`        | `tuple` | `(14, 19)`     |
| `PERFECT`     | `bool`  | `True`         |
| `OUTPUT_FILE` | `str`   | `"maze.txt"`   |

---

## Point d'entrée principal

```python
if __name__ == "__main__":
    config  = load_config("config.txt")          # 1. lire la config
    mg      = Maze_Generator(config["WIDTH"],     # 2. créer le générateur
                             config["HEIGHT"])
    mg.generate(seed=42)                          # 3. générer le labyrinthe
    display = MazeDisplay(mg,                     # 4. créer l'affichage
                          config["ENTRY"],
                          config["EXIT"])
    display.path = mg.solve(config["ENTRY"],      # 5. calculer le chemin
                            config["EXIT"])
    display.run()                                 # 6. lancer la fenêtre
```

---

## Format du fichier de configuration

```
# Ceci est un commentaire
WIDTH=20
HEIGHT=15
ENTRY=0,0
EXIT=14,19
OUTPUT_FILE=maze.txt
PERFECT=True
SEED=42
```

**Règles :**

- Une paire `CLÉ=VALEUR` par ligne
- Les lignes commençant par `#` sont ignorées
- Les lignes vides sont ignorées
- `ENTRY` et `EXIT` sont au format `row,col`

---

## Format du fichier de sortie

```
9515...    ← ligne 0 du labyrinthe (1 hex par cellule)
EBAB...    ← ligne 1
...
C545...    ← dernière ligne
           ← ligne vide obligatoire
0,0        ← coordonnées d'entrée
14,19      ← coordonnées de sortie
SSEENEE... ← chemin le plus court (N/S/E/W)
```

---

## Encodage des murs (bits)

Chaque cellule est un entier 4 bits (0 à F en hexadécimal) :

```
bit 0 (valeur 1) → mur Nord
bit 1 (valeur 2) → mur Est
bit 2 (valeur 4) → mur Sud
bit 3 (valeur 8) → mur Ouest

bit = 1 → mur FERMÉ (obstacle)
bit = 0 → mur OUVERT (passage)
```

**Exemples :**

| Hex | Binaire | Murs présents                    |
|-----|---------|----------------------------------|
| `0` | `0000`  | Aucun                            |
| `1` | `0001`  | Nord                             |
| `5` | `0101`  | Nord + Sud                       |
| `A` | `1010`  | Est + Ouest                      |
| `F` | `1111`  | Nord + Est + Sud + Ouest (fermée) |

**Opérations bit à bit utilisées dans le code :**

```python
# Vérifier si le mur Nord est présent
(cell & 1) != 0

# Ouvrir le mur Est (casser le passage)
cell &= ~2   # met le bit 1 à 0

# Fermer le mur Sud (ajouter un mur)
cell |= 4    # met le bit 2 à 1
```

---

## Touches clavier MLX

| Touche           | Keycode X11 |
|------------------|-------------|
| `Escape`         | 65307       |
| `1`              | 49          |
| `2`              | 50          |
| `3`              | 51          |
| `4`              | 52          |
| `Flèche haut`    | 65362       |
| `Flèche bas`     | 65364       |
| `Flèche gauche`  | 65361       |
| `Flèche droite`  | 65363       |
| `Espace`         | 32          |
| `Entrée`         | 65293       |

> Pour trouver le keycode d'une touche inconnue, ajoute temporairement
> `print(keycode)` dans le callback `on_key`.

---

*Documentation générée pour le projet A-Maze-ing — 42 School*
