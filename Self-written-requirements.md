# Estructura que busco en el articulo

### Resumen del articulo

Este articulo busca proponer una arquitectura e implementación basica de una herramienta, especializada en la solución de  problemas algebraicos, especificamente ecuaciones lineales de una sola variable

La implementación se hará mediante un sistema deterministico con una heuristica pedagogica, que al ser determinista no cuenta con fallos matematicos, ni alucinaciones

Por otro lado este sistema optimiza el uso de recursos, ya que es capaz de contar con LLMs mas pequeños y de menores capacidades y contando con la misma efectividad

La última parte que se propone realizar es la de implementar animaciones realizadas con el motor de *manim* la cual es una librería de python especializada en lo antes mencionado



### Puntos importantes propuestos a tratar



#### Estado del arte

Esta sección es la encargada de reunir la información necesaria de diversas implementaciones existentes, en este caso lo que se busca es el de encontrar fortalezas y debilidades de cada una de ellas

el punto de este es la de fortaleces aún mas los  argumentos que se tienen (Es local, es ligero, es efectivo y es personalizado)

#### Planteamiento de la solución

Esta sección es mas que nada técnica, encargada de explicar y justificar las decisiones arquitectonicas del software, tambien dando pie a las posibles implementaciones de un sistema completo 

#### Pruebas y discusión

Después de proponer las arquitecturas, considero necesario hacer pruebas de rendimiento, principalmente dos:

- Una prueba de efectividad resolviendo diversas ecuaciones cuando se cuenta con la herramienta y cuando es únicamente el LLM "pensando" por si mismo
- Una prueba de tiempo de ejecución para comparar que tan viable es la implementación de estos materiales 
