# Connect Academy — Landing Page

Landing page comercial do **Connect Academy**, a escola de negócios e inteligência
corporativa do ecossistema **Connect Valley**.

Construída a partir do folder institucional 2026 e do Manual de Marca do RF Group.

## Stack

- **React 18** — componentes funcionais com hooks
- **Tailwind CSS 3** — cores da marca via classes arbitrárias (`bg-[#14193C]`, `text-[#F5CD55]`)
- **lucide-react** — ícones (`Target`, `Users`, `Cpu`, `Briefcase`, `Scale`, `TrendingUp`,
  `Calendar`, `MessageCircle`, `CheckCircle2`, entre outros)
- **Framer Motion** — animações sutis de entrada (`whileInView`, `once: true`)
- **Vite 6** — build e dev server

## Paleta (Manual de Marca)

| Uso | Hex |
|---|---|
| Fundo principal / Dark Navy | `#14193C` |
| Destaque / Amarelo Ouro | `#F5CD55` |
| Cinza neutro / texto secundário | `#727272` |
| Branco | `#FFFFFF` |
| Profundidade de degradê (derivado do navy) | `#0D1129` |

Estilo visual: dark mode elegante, glassmorphism em tom navy (`.glass` e `.glass-gold`
em `src/index.css`), bordas sutis douradas e degradês radiais suaves.

## Assets da marca

Os logos, badges de trilha e fotos em `src/assets/` foram **extraídos dos arquivos
oficiais** (Manual de Marca RF Group e Folder Connect Academy 2026) — nenhum foi
recriado. A procedência de cada arquivo está em [`src/assets/README.md`](src/assets/README.md).

## Como rodar

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # gera dist/
npm run preview    # serve o build de produção
npm run standalone # gera dist-standalone/connect-academy.html (arquivo único)
```

O `standalone` embute CSS, JS, imagens e a fonte Poppins como data URI e produz uma
página sem nenhuma requisição externa — para abrir offline com duplo clique, enviar
por e-mail/WhatsApp ou publicar onde a política de segurança bloqueia CDNs.

## Estrutura

```
src/
  ConnectAcademyLanding.jsx   # página completa em arquivo único (autocontido)
  App.jsx                     # apenas renderiza a landing
  main.jsx                    # bootstrap do React
  index.css                   # Tailwind + utilitários .glass / .glass-gold / .gold-text
  assets/                     # logos, badges e fotos oficiais + README de procedência
scripts/
  build-standalone.mjs        # gera a versão em arquivo único
tailwind.config.js            # keyframes float / shine / pulse-ring
index.html                    # meta tags, OG e fonte Poppins
```

O componente é **autocontido**: para reaproveitar em outro projeto que já use Tailwind,
basta copiar `src/ConnectAcademyLanding.jsx` (e as classes `.glass`, `.glass-gold`,
`.gold-text` de `src/index.css`) e importar `<ConnectAcademyLanding />`.

## Seções

1. **Header** — navbar fixa com blur ao rolar, menu mobile e CTA "Garantir vaga"
2. **Hero** — badge de datas, headline, CTAs (WhatsApp + âncora) e card de escassez com
   contador regressivo
3. **Sobre** — o que é o Connect Academy + os 4 pilares
4. **Imersões** — 6 trilhas: Connect Med (em destaque), G360, Connect RH, Connect IA,
   Connect Tributário e GrowBase. Cada card leva ao WhatsApp com mensagem pré-preenchida
   específica da trilha
5. **Diferenciais** — presencial e exclusiva, networking de alto nível, metodologia prática
   + faixa de datas com CTA
6. **CTA final + Footer** — WhatsApp, Instagram, navegação e copyright
7. **Botão flutuante** de WhatsApp

## Manutenção comercial

Todo o conteúdo editável está no topo de `src/ConnectAcademyLanding.jsx`:

| Constante | O que controla |
|---|---|
| `WHATSAPP_NUMBER` / `WHATSAPP_DISPLAY` | número de contato (`+55 88 9383-2512`) |
| `INSTAGRAM_HANDLE` / `INSTAGRAM_URL` | perfil `@connectacademyy` |
| `VAGAS_POR_TURMA` | escassez exibida na página (20) |
| `EVENT_DATE` | data-alvo do contador regressivo do hero |
| `TRACKS` | as 6 trilhas (nome, ícone, slogan, descrição, tópicos, destaque) |
| `DIFERENCIAIS` | os 3 diferenciais |
| `NAV_LINKS` | itens do menu |

> **Atenção ao `EVENT_DATE`.** O folder anuncia "PRÉ-EVENTO 18 FEV | IMERSÃO 19 E 20 FEV"
> sem indicar o ano. A constante está em `2027-02-18` para que o contador fique ativo;
> ajuste-a a cada nova turma. Se a data já tiver passado, o contador desaparece
> automaticamente e o card mantém apenas o alerta de vagas limitadas.

## Acessibilidade e responsividade

- Layout validado em 1440px e 390px sem overflow horizontal
- Foco visível (`focus-visible:ring`) em todos os CTAs
- `aria-label` / `aria-expanded` no menu mobile e nos links de contato
- `prefers-reduced-motion` respeitado em `src/index.css`
