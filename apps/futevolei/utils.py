FUTEVOLEI_TEMPLATES = {
	4: {
		'FASE 1': [
			{'jogo': 1, 'dupla1': '1', 'dupla2': '2'},
			{'jogo': 2, 'dupla1': '3', 'dupla2': '4'},
		],
		'FASE 2': [
			{'jogo': 3, 'dupla1': 'Vencedor Jogo 1', 'dupla2': 'Vencedor Jogo 2'}, # Final da Winners
			{'jogo': 4, 'dupla1': 'Perdedor Jogo 1', 'dupla2': 'Perdedor Jogo 2'}  # Repescagem
		],
		'FASE 3': [
			{'jogo': 5, 'dupla1': 'Vencedor Jogo 4', 'dupla2': 'Perdedor Jogo 3'}  # Vencedor da repescagem vs Perdedor da final winners
		],
		'FASE 4': [
			{'jogo': 6, 'dupla1': 'Vencedor Jogo 3', 'dupla2': 'Vencedor Jogo 5'}  # Se W5 ganhar, gera o Jogo 7 (Reset)
		],
	},
	8: {
		'FASE 1': [
			{'jogo': 1, 'dupla1': '1', 'dupla2': '2'},
			{'jogo': 2, 'dupla1': '3', 'dupla2': '4'},
			{'jogo': 3, 'dupla1': '5', 'dupla2': '6'},
			{'jogo': 4, 'dupla1': '7', 'dupla2': '8'},
		],
		'FASE 2': [
			{'jogo': 5, 'dupla1': 'Vencedor Jogo 1', 'dupla2': 'Vencedor Jogo 2'},
			{'jogo': 6, 'dupla1': 'Vencedor Jogo 3', 'dupla2': 'Vencedor Jogo 4'},
			{'jogo': 7, 'dupla1': 'Perdedor Jogo 1', 'dupla2': 'Perdedor Jogo 2'},
			{'jogo': 8, 'dupla1': 'Perdedor Jogo 3', 'dupla2': 'Perdedor Jogo 4'}
		],
		'FASE 3': [
			{'jogo': 9, 'dupla1': 'Vencedor Jogo 5', 'dupla2': 'Vencedor Jogo 6'},  # Final da Winners
			{'jogo': 10, 'dupla1': 'Vencedor Jogo 7', 'dupla2': 'Perdedor Jogo 6'}, # Loser da semi cai aqui
			{'jogo': 11, 'dupla1': 'Vencedor Jogo 8', 'dupla2': 'Perdedor Jogo 5'}, # Loser da semi cai aqui
		],
		'FASE 4': [
			{'jogo': 12, 'dupla1': 'Vencedor Jogo 10', 'dupla2': 'Vencedor Jogo 11'} # Semi da Losers
		],
		'FASE 5': [
			{'jogo': 13, 'dupla1': 'Vencedor Jogo 12', 'dupla2': 'Perdedor Jogo 9'}  # Final da Losers (contra perdedor da final winners)
		],
		'FASE 6': [
			{'jogo': 14, 'dupla1': 'Vencedor Jogo 9', 'dupla2': 'Vencedor Jogo 13'}  # Grande Final
		],
	},
	16: {
		'FASE 1': [
			{'jogo': 1, 'dupla1': '1', 'dupla2': '2'},
			{'jogo': 2, 'dupla1': '3', 'dupla2': '4'},
			{'jogo': 3, 'dupla1': '5', 'dupla2': '6'},
			{'jogo': 4, 'dupla1': '7', 'dupla2': '8'},
			{'jogo': 5, 'dupla1': '9', 'dupla2': '10'},
			{'jogo': 6, 'dupla1': '11', 'dupla2': '12'},
			{'jogo': 7, 'dupla1': '13', 'dupla2': '14'},
			{'jogo': 8, 'dupla1': '15', 'dupla2': '16'},
		],
		'FASE 2': [
			{'jogo': 9, 'dupla1': 'Vencedor Jogo 1', 'dupla2': 'Vencedor Jogo 2'},
			{'jogo': 10, 'dupla1': 'Vencedor Jogo 3', 'dupla2': 'Vencedor Jogo 4'},
			{'jogo': 11, 'dupla1': 'Vencedor Jogo 5', 'dupla2': 'Vencedor Jogo 6'},
			{'jogo': 12, 'dupla1': 'Vencedor Jogo 7', 'dupla2': 'Vencedor Jogo 8'},
			# Repescagem: Perdedores da primeira rodada se enfrentam
			{'jogo': 13, 'dupla1': 'Perdedor Jogo 1', 'dupla2': 'Perdedor Jogo 2'},
			{'jogo': 14, 'dupla1': 'Perdedor Jogo 3', 'dupla2': 'Perdedor Jogo 4'},
			{'jogo': 15, 'dupla1': 'Perdedor Jogo 5', 'dupla2': 'Perdedor Jogo 6'},
			{'jogo': 16, 'dupla1': 'Perdedor Jogo 7', 'dupla2': 'Perdedor Jogo 8'},
		],
		'FASE 3': [
			{'jogo': 17, 'dupla1': 'Vencedor Jogo 9', 'dupla2': 'Vencedor Jogo 10'},
			{'jogo': 18, 'dupla1': 'Vencedor Jogo 11', 'dupla2': 'Vencedor Jogo 12'},
			# Integração Losers: Vencedores da R1 vs Perdedores das Quartas da Winners
			{'jogo': 19, 'dupla1': 'Vencedor Jogo 13', 'dupla2': 'Perdedor Jogo 12'},
			{'jogo': 20, 'dupla1': 'Vencedor Jogo 14', 'dupla2': 'Perdedor Jogo 11'},
			{'jogo': 21, 'dupla1': 'Vencedor Jogo 15', 'dupla2': 'Perdedor Jogo 10'},
			{'jogo': 22, 'dupla1': 'Vencedor Jogo 16', 'dupla2': 'Perdedor Jogo 9'},
		],
		'FASE 4': [
			{'jogo': 23, 'dupla1': 'Vencedor Jogo 17', 'dupla2': 'Vencedor Jogo 18'}, # Final da Winners
			# Afunilamento da Losers
			{'jogo': 24, 'dupla1': 'Vencedor Jogo 19', 'dupla2': 'Vencedor Jogo 20'},
			{'jogo': 25, 'dupla1': 'Vencedor Jogo 21', 'dupla2': 'Vencedor Jogo 22'},
		],
		'FASE 5': [
			# Vencedores da Losers R3 vs Perdedores da Semi da Winners
			{'jogo': 26, 'dupla1': 'Vencedor Jogo 24', 'dupla2': 'Perdedor Jogo 18'},
			{'jogo': 27, 'dupla1': 'Vencedor Jogo 25', 'dupla2': 'Perdedor Jogo 17'},
		],
		'FASE 6': [
			{'jogo': 28, 'dupla1': 'Vencedor Jogo 26', 'dupla2': 'Vencedor Jogo 27'},
		],
		'FASE 7': [
			{'jogo': 29, 'dupla1': 'Vencedor Jogo 28', 'dupla2': 'Perdedor Jogo 23'}, # Vencedor da Losers vs Perdedor da Final Winners
		],
		'FASE 8': [
			{'jogo': 30, 'dupla1': 'Vencedor Jogo 23', 'dupla2': 'Vencedor Jogo 29'}, # FINAL
		]
	}
}