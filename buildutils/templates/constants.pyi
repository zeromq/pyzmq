from typing import Dict, Set, List

ctx_opts: Set[int]
bytes_sockopts: Set[int]
fd_sockopts: Set[int]
int_sockopts: Set[int]
int64_sockopts: Set[int]

ctx_opt_names: List[str]
bytes_sockopt_names: List[str]
fd_sockopt_names: List[str]
int_sockopt_names: List[str]
int64_sockopt_names: List[str]

socket_types: Dict[int, str]

DRAFT_API: bool

{constants}
