cutechess-cli.exe ^
-engine conf=lc0 ^
-engine conf=sf11 ^
-each proto=uci tc=80/300+1 ^
-pgnout "match-%1.pgn" ^
-event "match-%1" ^
-site "Feldis PC" ^
-recover ^
-concurrency 1 ^
-tournament gauntlet ^
-resign movecount=3 score=800 ^
-draw movenumber=50 movecount=5 score=8 ^
-ratinginterval 1 ^
-games 2 ^
-rounds 5 ^
-openings file="D:\chess\cutechess\Hert500.pgn" format=pgn order=random policy=round ^
-repeat ^
-debug > cute_debug_log_%1.txt
rem remis nach 100 zuegen -draw movenumber=100 movecount=1 score=9999