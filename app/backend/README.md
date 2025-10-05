Put all pure functionality (**non**-GUI) in here. 

Imports in modules from this package to other modules should either be relative or look like 
```python
from backend.<...> import <...>
```
or 
```python
import backend.<...> as <...>
```