# -*- coding: utf-8 -*-
"""
Script gerador de PDF puro em Python (sem dependências externas)
Gera o documento formatado 'prompt_portfolio_3d.pdf' para Matheus Oliveira de Carvalho (2º B TI)
"""

import os
import re

class PDFDoc:
    def __init__(self, filename="prompt_portfolio_3d.pdf"):
        self.filename = filename
        self.pages = []
        self.current_page_ops = []
        self.width = 595.28   # A4 largura em pontos
        self.height = 841.89  # A4 altura em pontos

    def new_page(self):
        if self.current_page_ops:
            self.pages.append(self.current_page_ops)
        self.current_page_ops = []

    def rect(self, x, y, w, h, fill_color=None, stroke_color=None, stroke_width=1):
        ops = []
        if stroke_color:
            r, g, b = stroke_color
            ops.append(f"{r:.3f} {g:.3f} {b:.3f} RG")
            ops.append(f"{stroke_width} w")
        if fill_color:
            r, g, b = fill_color
            ops.append(f"{r:.3f} {g:.3f} {b:.3f} rg")
        ops.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re")
        if fill_color and stroke_color:
            ops.append("B")
        elif fill_color:
            ops.append("f")
        elif stroke_color:
            ops.append("S")
        self.current_page_ops.append("\n".join(ops))

    def line(self, x1, y1, x2, y2, color=(0.15, 0.88, 0.76), width=1):
        r, g, b = color
        op = f"{r:.3f} {g:.3f} {b:.3f} RG\n{width} w\n{x1:.2f} {y1:.2f} m\n{x2:.2f} {y2:.2f} l\nS"
        self.current_page_ops.append(op)

    def escape_text(self, text):
        # Converte caracteres para WinAnsiEncoding bytes e escapa caracteres especiais do PDF
        encoded = text.encode('windows-1252', errors='replace')
        out = []
        for b in encoded:
            c = chr(b)
            if c in ('\\', '(', ')'):
                out.append('\\' + c)
            elif 32 <= b <= 126 or b >= 160:
                out.append(c)
            else:
                out.append(f"\\{b:03o}")
        return "".join(out)

    def draw_text(self, text, x, y, font="F1", size=10, color=(0, 0, 0)):
        r, g, b = color
        safe_str = self.escape_text(text)
        op = f"BT\n/{font} {size} Tf\n{r:.3f} {g:.3f} {b:.3f} rg\n{x:.2f} {y:.2f} Td\n({safe_str}) Tj\nET"
        self.current_page_ops.append(op)

    def wrap_text(self, text, max_chars=80):
        words = text.split(' ')
        lines = []
        cur = []
        cur_len = 0
        for w in words:
            if cur_len + len(w) + 1 > max_chars:
                lines.append(" ".join(cur))
                cur = [w]
                cur_len = len(w)
            else:
                cur.append(w)
                cur_len += len(w) + 1
        if cur:
            lines.append(" ".join(cur))
        return lines

    def draw_paragraph(self, text, x, y, font="F1", size=10, color=(0.2, 0.2, 0.2), leading=14, max_chars=85):
        lines = self.wrap_text(text, max_chars)
        cur_y = y
        for l in lines:
            self.draw_text(l, x, cur_y, font, size, color)
            cur_y -= leading
        return cur_y

    def build(self):
        if self.current_page_ops:
            self.pages.append(self.current_page_ops)

        objects = []
        
        # Objeto 1: Catálogo
        # Objeto 2: Pages
        # Objetos de páginas e fontes...
        total_pages = len(self.pages)
        page_obj_ids = [3 + i * 2 for i in range(total_pages)]

        # Fontes:
        # F1 = Helvetica
        # F2 = Helvetica-Bold
        # F3 = Helvetica-Oblique
        # F4 = Courier
        font_base_id = 3 + total_pages * 2
        f1_id = font_base_id
        f2_id = font_base_id + 1
        f3_id = font_base_id + 2
        f4_id = font_base_id + 3

        # Escreve PDF
        pdf_bytes = bytearray()
        pdf_bytes.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = {}

        def add_object(obj_num, body_bytes):
            offsets[obj_num] = len(pdf_bytes)
            pdf_bytes.extend(f"{obj_num} 0 obj\n".encode('ascii'))
            pdf_bytes.extend(body_bytes)
            pdf_bytes.extend(b"\nendobj\n")

        # 1: Catalog
        add_object(1, b"<< /Type /Catalog /Pages 2 0 R >>")

        # 2: Pages
        kids_str = " ".join([f"{pid} 0 R" for pid in page_obj_ids])
        pages_body = f"<< /Type /Pages /Kids [{kids_str}] /Count {total_pages} >>".encode('ascii')
        add_object(2, pages_body)

        # Páginas e Conteúdos
        for i, page_ops in enumerate(self.pages):
            pid = page_obj_ids[i]
            cid = pid + 1
            stream_content = "\n".join(page_ops).encode('latin1')
            
            page_body = (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.width:.2f} {self.height:.2f}] "
                f"/Contents {cid} 0 R "
                f"/Resources << /Font << "
                f"/F1 {f1_id} 0 R /F2 {f2_id} 0 R /F3 {f3_id} 0 R /F4 {f4_id} 0 R "
                f">> >> >>"
            ).encode('ascii')
            add_object(pid, page_body)

            content_body = (
                f"<< /Length {len(stream_content)} >>\nstream\n"
            ).encode('ascii') + stream_content + b"\nendstream"
            add_object(cid, content_body)

        # Fontes com WinAnsiEncoding
        add_object(f1_id, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
        add_object(f2_id, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
        add_object(f3_id, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding >>")
        add_object(f4_id, b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>")

        # Tabela xref
        xref_offset = len(pdf_bytes)
        total_objs = f4_id + 1
        pdf_bytes.extend(f"xref\n0 {total_objs}\n".encode('ascii'))
        pdf_bytes.extend(b"0000000000 65535 f \n")
        for obj_num in range(1, total_objs):
            offset = offsets.get(obj_num, 0)
            pdf_bytes.extend(f"{offset:010d} 00000 n \n".encode('ascii'))

        # Trailer
        trailer_str = (
            f"trailer\n<< /Size {total_objs} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        )
        pdf_bytes.extend(trailer_str.encode('ascii'))

        with open(self.filename, 'wb') as f:
            f.write(pdf_bytes)
        print(f"PDF gerado com sucesso: {self.filename} ({len(pdf_bytes)} bytes)")


def generate_portfolio_pdf():
    doc = PDFDoc("prompt_portfolio_3d.pdf")

    # Cores
    C_DARK = (0.027, 0.043, 0.098)     # #070b19
    C_CARD = (0.055, 0.082, 0.180)     # #0e152e
    C_TURQUOISE = (0.153, 0.882, 0.757)# #27E1C1
    C_PINK = (1.000, 0.239, 0.506)     # #FF3D81
    C_YELLOW = (1.000, 0.706, 0.000)   # #FFB400
    C_PURPLE = (0.424, 0.361, 0.906)   # #6C5CE7
    C_WHITE = (0.98, 0.98, 0.98)
    C_GRAY = (0.64, 0.72, 0.80)
    C_MUTED = (0.45, 0.52, 0.60)

    # ----------------------------------------------------
    # PÁGINA 1: CAPA & VISÃO GERAL
    # ----------------------------------------------------
    doc.new_page()
    # Fundo estilizado com cabeçalho escuro neon
    doc.rect(0, 0, 595.28, 841.89, fill_color=(0.96, 0.97, 0.99))
    doc.rect(0, 680, 595.28, 161.89, fill_color=C_DARK)
    doc.rect(0, 676, 595.28, 4, fill_color=C_TURQUOISE)

    # Títulos Cabeçalho
    doc.draw_text("PORTFÓLIO 3D • ESPECIFICAÇÃO & PROMPT", 40, 800, "F2", 12, C_TURQUOISE)
    doc.draw_text("Matheus Oliveira de Carvalho", 40, 765, "F2", 24, C_WHITE)
    doc.draw_text("Estudante do Curso Técnico em TI • Turma 2º B TI", 40, 742, "F1", 13, C_YELLOW)
    doc.draw_text("Guia Técnico do Projeto Web 3D • Three.js • GSAP • Efeitos Cinemáticos", 40, 722, "F3", 10, C_GRAY)

    # Caixa de Destaque do Pedido
    doc.rect(40, 560, 515.28, 95, fill_color=(1, 1, 1), stroke_color=(0.85, 0.88, 0.92), stroke_width=1)
    doc.rect(40, 560, 6, 95, fill_color=C_PINK)
    doc.draw_text("1. O PEDIDO ORIGINAL (TEXTO DO USUÁRIO)", 56, 635, "F2", 11, C_PINK)
    p_orig = (
        '"faca um portfolio para mim em um prompt com documento para que seja igual aplicativos 3d com as '
        'partes em movimentos mas que seja colorido ai coloca no documento todo prompt que eu te falei e coloque '
        'meu nome ai me mande o prompt e dps me mande em pdf o documento do prompt, mas deixe mais ele em 3d e '
        'que tenha referencias a sites que tem a ultilizacao de movimentos 3d"'
    )
    doc.draw_paragraph(p_orig, 56, 615, "F3", 9, (0.2, 0.25, 0.3), leading=13, max_chars=82)

    # O que foi entregue
    doc.rect(40, 415, 515.28, 130, fill_color=(1, 1, 1), stroke_color=(0.85, 0.88, 0.92), stroke_width=1)
    doc.rect(40, 415, 6, 130, fill_color=C_TURQUOISE)
    doc.draw_text("O QUE FOI DESENVOLVIDO & ENTREGUE", 56, 525, "F2", 11, C_TURQUOISE)

    items_entregues = [
        "• Arquivo Completo index.html: Aplicação 3D pronta para abrir no navegador ou subir no GitHub Pages.",
        "• Tridimensionalidade Real: Cena WebGL com Three.js, iluminação neon, partículas e piso em grade com perspectiva.",
        "• Núcleo 3D Interativo: Icosaedro holográfico central que reage ao mouse e arrasto com inércia física.",
        "• Cartões 3D com Tilt & Giro: Efeito de inclinação no Sobre Mim e giro 360º interativo nas Habilidades.",
        "• Projeto em Destaque: LifeRPG com link direto (https://gabriel-vequeti.github.io/teste/) e cards imersivos.",
        "• Controles Dinâmicos: Teclas de atalho (T para temas, P para pausar, Setas), sintetizador de áudio e 3 paletas."
    ]
    cur_y = 505
    for it in items_entregues:
        doc.draw_text(it, 56, cur_y, "F1", 9, (0.15, 0.20, 0.25))
        cur_y -= 15

    # Caixa de Identidade Visual
    doc.rect(40, 260, 515.28, 140, fill_color=C_DARK, stroke_color=C_TURQUOISE, stroke_width=1)
    doc.draw_text("IDENTIDADE VISUAL & PALETA NEON 3D", 56, 375, "F2", 12, C_WHITE)
    doc.draw_text("Visual inspirado nos designs mais premiados do Awwwards e estúdios WebGL internacionais:", 56, 355, "F1", 9.5, C_GRAY)

    # Quadrados de cores da paleta
    cores_demonstradas = [
        ("Rosa Neon", "#FF3D81", C_PINK, 56),
        ("Turquesa", "#27E1C1", C_TURQUOISE, 150),
        ("Amarelo", "#FFB400", C_YELLOW, 244),
        ("Roxo Neon", "#6C5CE7", C_PURPLE, 338),
        ("Azul Cyber", "#00B4FF", (0, 0.7, 1), 432)
    ]
    for nome, hex_val, col, x_pos in cores_demonstradas:
        doc.rect(x_pos, 305, 75, 32, fill_color=col)
        doc.draw_text(nome, x_pos, 290, "F2", 8.5, C_WHITE)
        doc.draw_text(hex_val, x_pos, 278, "F4", 8, C_GRAY)

    # Rodapé da Página 1
    doc.line(40, 50, 555.28, 50, color=(0.8, 0.85, 0.9), width=1)
    doc.draw_text("Portfólio 3D • Matheus Oliveira de Carvalho (Turma 2º B TI)", 40, 36, "F1", 9, C_MUTED)
    doc.draw_text("Página 1 de 4", 500, 36, "F1", 9, C_MUTED)

    # ----------------------------------------------------
    # PÁGINA 2: O PROMPT COMPLETO
    # ----------------------------------------------------
    doc.new_page()
    doc.rect(0, 0, 595.28, 841.89, fill_color=(0.96, 0.97, 0.99))
    doc.rect(0, 770, 595.28, 71.89, fill_color=C_DARK)
    doc.rect(0, 766, 595.28, 4, fill_color=C_PINK)

    doc.draw_text("2. O PROMPT COMPLETO (PRONTO PARA COLAR EM QUALQUER IA)", 40, 805, "F2", 12, C_PINK)
    doc.draw_text("Copie o conteúdo da caixa abaixo para recriar ou expandir o portfólio:", 40, 785, "F3", 9.5, C_GRAY)

    # Caixa do Prompt em estilo terminal / código
    doc.rect(40, 70, 515.28, 680, fill_color=C_DARK, stroke_color=C_TURQUOISE, stroke_width=1)

    prompt_lines = [
        ("PAPEL:", "Voce e um desenvolvedor front-end senior e diretor criativo, especialista em experiencias 3D na web."),
        ("OBJETIVO:", "Criar o portfolio pessoal de Matheus Oliveira de Carvalho como um unico arquivo index.html"),
        ("", "(HTML + CSS + JavaScript), que pareca um aplicativo 3D: objetos flutuando, partes em movimento,"),
        ("", "camera que reage ao mouse e ao scroll, tudo muito colorido."),
        ("TECNOLOGIAS:", "Three.js (CDN), GSAP + ScrollTrigger (CDN), CSS moderno (variaveis, gradientes, glassmorphism,"),
        ("", "3D transforms). Sem frameworks obrigatorios. Codigo 100% organizado e amplamente comentado."),
        ("ESTILO VISUAL:", "Fundo escuro azul-noite com gradientes vivos. Paleta neon: rosa #FF3D81, amarelo #FFB400,"),
        ("", "turquesa #27E1C1, roxo #6C5CE7, azul #00B4FF, verde #8AFF4D. Materiais brilhantes, sombras"),
        ("", "suaves, efeito de profundidade (parallax, blur de fundo, neblina). Tipografia moderna."),
        ("CENA 3D:", "- Formas geometricas coloridas (cubos, esferas, toros, icosaedros) flutuando e girando."),
        ("", "- Objeto central de destaque (icosaedro/nucleo) que gira devagar e reage ao mouse e toque."),
        ("", "- Particulas coloridas ao fundo e um piso em grade com perspectiva neon."),
        ("", "- A camera se move suavemente com mouse (parallax) e com o scroll (passeio tridimensional)."),
        ("", "- Animacoes continuas e leves: respiracao, flutuacao, rotacao e pulso de luz."),
        ("SECOES:", "1. Hero: nome 'Matheus Oliveira de Carvalho', turma '2o B TI', cargo/titulo, botoes 'Ver projetos'"),
        ("", "   e 'Contato'. Titulo com efeito de extrusao 3D."),
        ("", "2. Sobre mim: texto curto + cartao com tilt 3D (inclina seguindo as coordenadas do mouse)."),
        ("", "3. Habilidades: cubos/cartoes giratorios, cada habilidade em uma cor da paleta neon."),
        ("", "4. Projetos: cartoes 3D que viram e levantam no hover; incluir o projeto LifeRPG"),
        ("", "   com link funcional para https://gabriel-vequeti.github.io/teste/ e outros destaques."),
        ("", "5. Experiencia / Linha do tempo: marcos que surgem em profundidade (eixo Z) com o scroll."),
        ("", "6. Contato: formulario simples com feedback toast + links de redes em botoes com brilho."),
        ("INTERACOES:", "Cursor personalizado colorido; hover com brilho e inclinacao; transicoes suaves;"),
        ("", "menu fixo translucido com blur; botoes para paletas de cores, som e pausa."),
        ("ACOES 3D:", "- Mouse: camera e objetos seguem o cursor; clique em forma 3D pula, troca cor e gera particulas."),
        ("", "- Arrastar: girar o objeto central com mouse ou dedo com inercia suave."),
        ("", "- Scroll: camera percorre a cena e secoes entram com profundidade."),
        ("", "- Hover projetos: cartao inclina em 3D, brilha e exibe botao 'Abrir projeto'."),
        ("", "- Habilidades: clique faz o card girar 360 graus e mostra nivel da habilidade."),
        ("", "- Teclado: setas navegam, T troca paleta (Neon, Sunset, Ocean), P pausa animacoes."),
        ("", "- Audio: efeitos sonoros espaciais gerados via Web Audio API (desligado por padrao)."),
        ("", "- Tela de carregamento: cubo girando em 3D e contador percentual de 0 a 100%."),
        ("QUALIDADE:", "60 FPS, limitar pixel ratio a 2, pausar quando aba oculta, responsivo e fallback CSS.")
    ]

    p_y = 730
    for prefix, content in prompt_lines:
        if prefix:
            doc.draw_text(prefix, 56, p_y, "F2", 8.2, C_YELLOW)
            doc.draw_text(content, 140, p_y, "F4", 7.8, C_WHITE)
        else:
            doc.draw_text(content, 140, p_y, "F4", 7.8, (0.75, 0.85, 0.95))
        p_y -= 16.5

    # Rodapé da Página 2
    doc.line(40, 50, 555.28, 50, color=(0.8, 0.85, 0.9), width=1)
    doc.draw_text("Portfólio 3D • Matheus Oliveira de Carvalho (Turma 2º B TI)", 40, 36, "F1", 9, C_MUTED)
    doc.draw_text("Página 2 de 4", 500, 36, "F1", 9, C_MUTED)

    # ----------------------------------------------------
    # PÁGINA 3: AÇÕES E INTERAÇÕES 3D IMPLEMENTADAS
    # ----------------------------------------------------
    doc.new_page()
    doc.rect(0, 0, 595.28, 841.89, fill_color=(0.96, 0.97, 0.99))
    doc.rect(0, 770, 595.28, 71.89, fill_color=C_DARK)
    doc.rect(0, 766, 595.28, 4, fill_color=C_YELLOW)

    doc.draw_text("3. AÇÕES E INTERAÇÕES IMPLEMENTADAS NO PORTFÓLIO", 40, 805, "F2", 12, C_YELLOW)
    doc.draw_text("Todas as 10 ações sugeridas no briefing foram programadas e validadas:", 40, 785, "F3", 9.5, C_GRAY)

    actions = [
        ("Mouse & Raycasting 3D", 
         "A câmera e os objetos seguem a posição do cursor em tempo real com interpolação suave (lerp). "
         "Clicar em qualquer objeto 3D flutuante faz a forma pular em escala elástica, trocar aleatoriamente de cor neon "
         "e explodir um anel de mini partículas brilhantes no espaço tridimensional.",
         C_TURQUOISE),

        ("Arrastar com Inércia (Drag Controls)", 
         "O usuário pode clicar ou tocar no canvas e arrastar para rotacionar o núcleo 3D central livremente. "
         "O movimento possui física de atrito (damping), desacelerando suavemente após soltar.",
         C_PINK),

        ("Câmera Guiada pelo Scroll (3D Tour)", 
         "Ao rolar a página para baixo ou para cima, a câmera viaja no eixo Z de 14 para 4 unidades, "
         "proporcionando um passeio cinematográfico que muda a perspectiva conforme cada seção é exibida.",
         C_YELLOW),

        ("Cartões com Tilt e Glassmorphism", 
         "Na seção Sobre Mim e Projetos, os cartões calculam a inclinação relativa ao cursor nos eixos X e Y, "
         "produzindo um efeito realista de cartão holográfico suspenso com reflexo luminoso.",
         C_PURPLE),

        ("Habilidades com Giro 360º", 
         "Ao clicar em qualquer cartão de tecnologia (HTML5, JS, Three.js, GSAP, etc.), o cartão executa um giro 3D completo "
         "de 360 graus com efeito sonoro e emite partículas 3D no centro da cena.",
         (0, 0.7, 1)),

        ("Teclas de Atalho Interativas", 
         "Teclas de navegação: [ ↑ ] e [ ↓ ] realizam rolagem suave entre as seções. Tecla [ T ] alterna instantaneamente "
         "a paleta de cores. Tecla [ P ] pausa ou continua todas as animações 3D da tela.",
         (0.2, 0.8, 0.4)),

        ("Alternador de Paletas Dinâmico", 
         "Cicla entre três temas completos: Neon Cyber (padrão), Sunset Glow (quente) e Ocean Depths (frio). "
         "Atualiza as luzes pontuais do Three.js, as cores dos materiais e as variáveis CSS em tempo de execução.",
         C_PINK),

        ("Sintetizador de Áudio (Web Audio API)", 
         "Efeitos sonoros procedurais gerados matematicamente direto pelo navegador sem necessitar de arquivos de áudio externos. "
         "Inicia desativado por padrão e pode ser ligado pelo botão na barra de navegação.",
         C_TURQUOISE)
    ]

    card_y = 660
    for title, desc, col in actions:
        doc.rect(40, card_y, 515.28, 62, fill_color=(1, 1, 1), stroke_color=(0.86, 0.89, 0.93), stroke_width=1)
        doc.rect(40, card_y, 5, 62, fill_color=col)
        doc.draw_text(title, 55, card_y + 45, "F2", 10.5, col)
        doc.draw_paragraph(desc, 55, card_y + 30, "F1", 8.5, (0.25, 0.3, 0.35), leading=12, max_chars=92)
        card_y -= 74

    # Rodapé da Página 3
    doc.line(40, 50, 555.28, 50, color=(0.8, 0.85, 0.9), width=1)
    doc.draw_text("Portfólio 3D • Matheus Oliveira de Carvalho (Turma 2º B TI)", 40, 36, "F1", 9, C_MUTED)
    doc.draw_text("Página 3 de 4", 500, 36, "F1", 9, C_MUTED)

    # ----------------------------------------------------
    # PÁGINA 4: REFERÊNCIAS 3D & GUIA DE PUBLICAÇÃO
    # ----------------------------------------------------
    doc.new_page()
    doc.rect(0, 0, 595.28, 841.89, fill_color=(0.96, 0.97, 0.99))
    doc.rect(0, 770, 595.28, 71.89, fill_color=C_DARK)
    doc.rect(0, 766, 595.28, 4, fill_color=C_TURQUOISE)

    doc.draw_text("4. REFERÊNCIAS DE SITES COM MOVIMENTO 3D & PUBLICAÇÃO", 40, 805, "F2", 12, C_TURQUOISE)
    doc.draw_text("Links e fontes de inspiração para evolução contínua das habilidades WebGL:", 40, 785, "F3", 9.5, C_GRAY)

    refs = [
        ("Bruno Simon - bruno-simon.com", "O mais famoso portfólio 3D do mundo. Um carrinho dirigível em um mundo com física real."),
        ("Three.js Examples - threejs.org/examples", "Galeria oficial de centenas de demonstrações de shaders, iluminação, geometrias e pós-processamento."),
        ("Spline 3D - spline.design", "Ferramenta intuitiva de design e exportação 3D para web com eventos de mouse e scroll."),
        ("Awwwards 3D Category - awwwards.com/websites/3d", "Vitrine dos projetos web 3D mais votados e premiados do design mundial."),
        ("Active Theory - activetheory.net", "Estúdio de vanguarda responsável pelas experiências WebGL mais imersivas da web."),
        ("Lusion - lusion.co", "Estúdio pioneiro em simulação física de partículas e superfícies orgânicas interativas.")
    ]

    r_y = 665
    for site, desc in refs:
        doc.rect(40, r_y, 515.28, 42, fill_color=(1, 1, 1), stroke_color=(0.86, 0.89, 0.93), stroke_width=1)
        doc.rect(40, r_y, 4, 42, fill_color=C_PURPLE)
        doc.draw_text(site, 54, r_y + 26, "F2", 9.5, C_DARK)
        doc.draw_text(desc, 54, r_y + 12, "F1", 8.2, (0.35, 0.4, 0.45))
        r_y -= 50

    # Seção 5: Guia de Publicação no GitHub Pages
    doc.rect(40, 95, 515.28, 245, fill_color=C_DARK, stroke_color=C_TURQUOISE, stroke_width=1)
    doc.draw_text("5. GUIA RÁPIDO: COMO PUBLICAR NO GITHUB PAGES", 56, 315, "F2", 11, C_TURQUOISE)

    steps = [
        "Passo 1: Crie uma conta no GitHub (se ainda não tiver) e crie um novo repositório público (ex: portfolio-3d).",
        "Passo 2: Envie o arquivo index.html que está salvo na sua pasta para a raiz desse repositório.",
        "Passo 3: No GitHub, acesse a aba Settings (Configurações) > Pages (no menu lateral esquerdo).",
        "Passo 4: Em 'Branch', selecione main (ou master) e pasta /root, depois clique em Save.",
        "Passo 5: Aguarde 1 a 2 minutos. O GitHub gerará seu link público gratuito (ex: seu-usuario.github.io/portfolio-3d)!",
        "",
        "COMO PERSONALIZAR SEUS DADOS NO index.html:",
        "• Abra o arquivo index.html no Bloco de Notas ou VS Code.",
        "• Procure por 'matheus.carvalho@email.com' e substitua pelo seu e-mail real.",
        "• Procure pelos links de GitHub e LinkedIn na seção de Contato e coloque seus perfis.",
        "• Para adicionar mais projetos, copie e cole o bloco de '<div class=\"project-card-3d\">'."
    ]

    s_y = 292
    for s in steps:
        if s.startswith("COMO"):
            doc.draw_text(s, 56, s_y, "F2", 8.5, C_YELLOW)
        elif s:
            doc.draw_text(s, 56, s_y, "F1", 8.2, (0.85, 0.90, 0.96))
        s_y -= 14

    # Rodapé da Página 4
    doc.line(40, 50, 555.28, 50, color=(0.8, 0.85, 0.9), width=1)
    doc.draw_text("Portfólio 3D • Matheus Oliveira de Carvalho (Turma 2º B TI)", 40, 36, "F1", 9, C_MUTED)
    doc.draw_text("Página 4 de 4", 500, 36, "F1", 9, C_MUTED)

    doc.build()

if __name__ == '__main__':
    generate_portfolio_pdf()

