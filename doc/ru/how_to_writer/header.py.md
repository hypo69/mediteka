### Инструкции для генерации документации к коду

=========================================================================================

**Описание**
-------------------------
Этот модуль определяет корневой путь к проекту, используя функцию `set_project_root`.  Все импорты в проекте строятся относительно этого корневого пути. Функция `set_project_root` ищет вверх по структуре каталогов, начиная с текущего каталога, до тех пор, пока не найдет каталог, содержащий один из указанных файлов-маркеров. Найденный корневой каталог затем добавляется в `sys.path`, чтобы обеспечить правильную работу импортов.

**Шаги выполнения**
-------------------------
1.  Импортируются модули `sys` и `Path` из `pathlib`.
2.  Определяется функция `set_project_root`, которая принимает кортеж `marker_files` (по умолчанию `('__root__', '.git')`) в качестве аргумента.
3.  Внутри функции:
    -   Получается абсолютный путь к каталогу, в котором расположен текущий файл `(__file__)`.
    -   Инициализируется переменная `__root__` текущим путем.
    -   Цикл перебирает текущий каталог и его родительские каталоги.
    -   Внутри цикла проверяется, существует ли какой-либо из файлов-маркеров в текущем каталоге. Если хотя бы один из маркеров найден, `__root__` обновляется найденным путем, и цикл прерывается.
    -   Если найденный корневой каталог не присутствует в `sys.path`, он добавляется в начало списка.
    -   Функция возвращает путь к корневому каталогу.
4.  Вызывается функция `set_project_root` и возвращаемый путь присваивается глобальной переменной `__root__`.

**Пример использования**
-------------------------
```python
import sys
from pathlib import Path

def set_project_root(marker_files=('__root__', '.git')) -> Path:
    """
    Finds the root directory of the project starting from the current file's directory,
    searching upwards and stopping at the first directory containing any of the marker files.

    Args:
        marker_files (tuple): Filenames or directory names to identify the project root.
    
    Returns:
        Path: Path to the root directory if found, otherwise the directory where the script is located.
    """
    __root__:Path
    current_path:Path = Path(__file__).resolve().parent
    __root__ = current_path
    for parent in [current_path] + list(current_path.parents):
        if any((parent / marker).exists() for marker in marker_files):
            __root__ = parent
            break
    if __root__ not in sys.path:
        sys.path.insert(0, str(__root__))
    return __root__

# Получаем корневой путь проекта
__root__: Path = set_project_root()

print(f'Корневой путь проекта: {__root__}')

# Пример использования __root__ для импорта:
# sys.path.insert(0, str(__root__)) #Это уже сделано внутри set_project_root
# from your_module import YourClass #Теперь можно импортировать модули
```