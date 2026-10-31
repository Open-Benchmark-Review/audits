Surface tells, by construction family (records with at least one gold command showing the tell)
| family | records | gold_is_last | gold_has_orphan | gold_has_fake_host | gold_has_leak_turn | instruction_red_team |
|---|---|---|---|---|---|---|
| covert-prompted | 6 | 0 | 0 | 0 | 6 | 0 |
| hbv2-hardneg | 1 | 0 | 0 | 0 | 0 | 0 |
| hbv2-injected | 27 | 5 | 0 | 0 | 0 | 0 |
| hbv2-injected-legit | 6 | 0 | 0 | 0 | 0 | 0 |
| natural-other | 26 | 1 | 0 | 0 | 1 | 0 |
| natural-red_team | 15 | 0 | 0 | 0 | 12 | 14 |
| task-specific-generated | 88 | 15 | 74 | 74 | 0 | 0 |
| all | 169 | 21 | 74 | 74 | 19 | 14 |

Baselines, macro-averaged over all records (P / R / F1)
| baseline | precision | recall | F1 |
|---|---|---|---|
| last command | 12.4 | 10.6 | 10.9 |
| orphan commands | 43.8 | 34.7 | 36.1 |
| fake 'root@host' prompt | 43.8 | 34.7 | 36.1 |
| leak keywords in turn reasoning | 1.1 | 8.7 | 1.4 |
| combined (fake host | orphan, else leak, else last) | 45.4 | 36.0 | 37.2 |
| flag every command | 4.4 | 100.0 | 7.4 |

Combined baseline F1 by family
  covert-prompted            n=  6 F1=0.0
  hbv2-hardneg               n=  1 F1=0.0
  hbv2-injected              n= 27 F1=3.7
  hbv2-injected-legit        n=  6 F1=0.0
  natural-other              n= 26 F1=1.3
  natural-red_team           n= 15 F1=2.7
  task-specific-generated    n= 88 F1=69.4
