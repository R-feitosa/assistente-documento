/**
 * CONNECT ACADEMY — Landing Page comercial
 * Escola de negócios e inteligência corporativa do ecossistema Connect Valley.
 *
 * Stack: React 18 + Tailwind CSS + lucide-react + framer-motion
 *
 * Todos os logos, badges de trilha e fotos em `src/assets/` foram extraídos dos
 * arquivos oficiais da marca — Manual de Marca RF Group e Folder Connect Academy
 * 2026 — e não recriados. Ver `src/assets/README.md` para a procedência de cada um.
 *
 * Paleta oficial (Manual de Marca RF Group):
 *   Dark Navy  #14193C   |  Amarelo Ouro #F5CD55
 *   Cinza      #727272   |  Branco       #FFFFFF
 * (#0D1129 aparece apenas como profundidade de degradê do navy principal)
 *
 * Arquivo único e autocontido: basta importar <ConnectAcademyLanding /> em qualquer app
 * com Tailwind configurado.
 */

import { useEffect, useId, useRef, useState } from 'react'
import { motion, useInView, useReducedMotion } from 'framer-motion'
import {
  ArrowRight,
  Briefcase,
  Calendar,
  CheckCircle2,
  ChevronDown,
  Compass,
  Cpu,
  Instagram,
  Layers,
  Lightbulb,
  MapPin,
  Menu,
  MessageCircle,
  Network,
  Scale,
  Stethoscope,
  TrendingUp,
  Users,
  X,
} from 'lucide-react'

/* Assets oficiais da marca (extraídos do Manual de Marca e do Folder 2026) */
import logoConnectAcademy from './assets/logo-connect-academy.png'
import logoConnectMed from './assets/logo-connect-med.webp'
import targetAlvo from './assets/target-alvo.webp'
import targetFlecha from './assets/target-flecha.webp'
import badgeG360 from './assets/badge-g360.png'
import badgeRh from './assets/badge-rh.png'
import badgeIa from './assets/badge-ia.png'
import badgeTributario from './assets/badge-tributario.png'
import badgeGrowbase from './assets/badge-growbase.png'
import fotoEvento1 from './assets/evento-1.webp'
import fotoEvento2 from './assets/evento-2.webp'
import fotoEquipeMed from './assets/connect-med-equipe.webp'
import selo20Vagas from './assets/selo-20-vagas.png'

/* -------------------------------------------------------------------------- */
/*  Dados da página — centralizados para facilitar a manutenção comercial      */
/* -------------------------------------------------------------------------- */

const WHATSAPP_NUMBER = '558893832512'
const WHATSAPP_DISPLAY = '+55 88 9383-2512'
const INSTAGRAM_HANDLE = 'connectacademyy'
const INSTAGRAM_URL = 'https://instagram.com/connectacademyy'
const VAGAS_POR_TURMA = 20

/**
 * Data do PRÉ-EVENTO usada pelo contador regressivo do Hero.
 * O folder anuncia "PRÉ-EVENTO 18 FEV | IMERSÃO 19 E 20 FEV" — ajuste o ano
 * a cada nova turma. Se a data já tiver passado, o contador some e o card
 * exibe apenas o alerta de escassez de vagas.
 */
const EVENT_DATE = '2027-02-18T09:00:00-03:00'

const waLink = (mensagem) =>
  `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(mensagem)}`

const WA_GERAL = waLink(
  'Olá! Vim pelo site do Connect Academy e quero conhecer as próximas turmas.',
)

const NAV_LINKS = [
  { label: 'Sobre', href: '#sobre' },
  { label: 'Imersões', href: '#imersoes' },
  { label: 'Diferenciais', href: '#diferenciais' },
  { label: 'Contato', href: '#contato' },
]

const TRACKS = [
  {
    id: 'connect-med',
    nome: 'Connect Med',
    icon: Stethoscope,
    // Ganha bloco próprio, em largura total, fora da grade das demais trilhas
    lockup: logoConnectMed,
    destaque: true,
    // Os três eixos anunciados no folder, exibidos como selos
    eixos: ['Gestão Médica 360°', 'Inteligência Comercial', 'Tributário p/ médicos'],
    slogan: 'Medicina com visão de negócio.',
    chamada: 'Gestão e estratégia para uma carreira médica mais sustentável.',
    descricao:
      'Uma imersão para médicos que desejam transformar excelência clínica em uma carreira ou negócio bem gerido. O programa integra Gestão Médica 360°, Inteligência Comercial e Estratégia Tributária para organizar a operação, valorizar as horas trabalhadas e ampliar a rentabilidade com ética e segurança.',
    topicos: [
      'Gestão Médica 360°',
      'Inteligência Comercial',
      'Tributário para médicos',
      'Precificação das horas trabalhadas',
      'Rentabilidade com ética e segurança',
    ],
  },
  {
    id: 'g360',
    nome: 'Gestão 360° | G360',
    icon: Briefcase,
    badge: badgeG360,
    slogan: 'Quem enxerga o todo, decide melhor.',
    chamada: 'Enxergue a empresa por inteiro.',
    descricao:
      'Uma imersão para empresários e líderes que precisam integrar estratégia, pessoas, processos, finanças, operação e liderança. O G360 amplia a visão sobre o negócio, revela gargalos e fortalece a capacidade de decidir, executar e crescer com método.',
    topicos: [
      'Integrar áreas e processos',
      'Profissionalizar a gestão',
      'Desenvolver lideranças',
      'Tomar decisões com mais clareza',
      'Crescer com eficiência e controle',
    ],
  },
  {
    id: 'connect-rh',
    nome: 'Connect RH',
    icon: Users,
    badge: badgeRh,
    slogan: 'Empresas fortes começam com pessoas alinhadas.',
    chamada: 'Pessoas, cultura e estratégia na mesma direção.',
    descricao:
      'Uma imersão sobre o novo papel do RH: menos burocracia, mais impacto no negócio. O Connect RH apresenta práticas atuais para fortalecer cultura, desenvolver lideranças, elevar a produtividade e melhorar a atração e a retenção de talentos.',
    topicos: [
      'Estruturar uma gestão de pessoas estratégica',
      'Fortalecer a cultura organizacional',
      'Aprimorar processos de RH',
      'Desenvolver líderes',
      'Conectar pessoas e resultados',
    ],
  },
  {
    id: 'connect-ia',
    nome: 'Connect IA',
    icon: Cpu,
    badge: badgeIa,
    slogan: 'A IA não substitui estratégia. Ela potencializa quem sabe executar.',
    chamada: 'Inteligência artificial aplicada ao trabalho real.',
    descricao:
      'Uma imersão prática para profissionais e equipes que querem incorporar a IA às rotinas, automatizar tarefas e tomar decisões com mais agilidade. O foco não é apenas entender a tecnologia, mas utilizá-la para gerar eficiência e vantagem competitiva.',
    topicos: [
      'Aplicar IA no dia a dia',
      'Automatizar tarefas repetitivas',
      'Otimizar processos e rotinas',
      'Aumentar produtividade',
      'Decidir com mais inteligência',
    ],
  },
  {
    id: 'connect-tributario',
    nome: 'Connect Tributário',
    icon: Scale,
    badge: badgeTributario,
    slogan: 'Quem entende antes, adapta-se melhor.',
    chamada: 'Prepare sua empresa para o novo cenário fiscal.',
    descricao:
      'Uma imersão que traduz a Reforma Tributária para a realidade das empresas, conectando mudanças legais a seus impactos financeiros, fiscais e operacionais. Empresários e gestores aprendem a antecipar riscos, planejar adaptações e identificar oportunidades com segurança.',
    topicos: [
      'Compreender os impactos da Reforma',
      'Antecipar riscos fiscais e operacionais',
      'Preparar processos e equipes',
      'Identificar oportunidades estratégicas',
      'Decidir com mais segurança',
    ],
  },
  {
    id: 'growbase',
    nome: 'GrowBase',
    icon: TrendingUp,
    badge: badgeGrowbase,
    // Fecha a grade em largura total, equilibrando a linha final com o card em destaque
    wide: true,
    slogan: 'Escalar não é acelerar no escuro. É construir uma base sólida.',
    chamada: 'Crescimento exige base, método e direção.',
    descricao:
      'Uma solução para empresas que cresceram, mas ainda enfrentam processos desorganizados, gargalos operacionais e decisões pouco previsíveis. O GrowBase ajuda a estruturar a operação, definir prioridades e criar as condições necessárias para escalar com controle.',
    topicos: [
      'Organizar processos de crescimento',
      'Identificar gargalos',
      'Estruturar a operação',
      'Melhorar a tomada de decisão',
      'Crescer com previsibilidade',
    ],
  },
]

const DIFERENCIAIS = [
  {
    icon: MapPin,
    titulo: 'Imersão presencial e exclusiva',
    texto:
      'Turmas reduzidas, de apenas 20 participantes, para garantir profundidade, troca real e atenção individual em cada imersão.',
  },
  {
    icon: Network,
    titulo: 'Networking de alto nível',
    texto:
      'Você entra no ecossistema Connect Valley e se conecta a empresários, gestores e especialistas que decidem — dentro e fora da sala.',
  },
  {
    icon: Lightbulb,
    titulo: 'Metodologia prática',
    texto:
      'Nada de teoria solta: o conteúdo é aplicado aos desafios reais da sua empresa, para você sair com método e plano de ação.',
  },
]

/* -------------------------------------------------------------------------- */
/*  Utilitários de animação                                                    */
/* -------------------------------------------------------------------------- */

const fadeUp = {
  hidden: { opacity: 0, y: 28 },
  visible: { opacity: 1, y: 0 },
}

function Reveal({ children, delay = 0, className = '' }) {
  return (
    <motion.div
      className={className}
      variants={fadeUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: 0.6, delay, ease: [0.21, 0.47, 0.32, 0.98] }}
    >
      {children}
    </motion.div>
  )
}

/* -------------------------------------------------------------------------- */
/*  Blocos visuais reutilizáveis                                               */
/* -------------------------------------------------------------------------- */

function Logo({ className = 'h-11' }) {
  return (
    <a href="#topo" className="group inline-flex items-center" aria-label="Connect Academy — início">
      <img
        src={logoConnectAcademy}
        alt="Connect Academy"
        className={`${className} w-auto transition-transform duration-300 group-hover:scale-[1.03]`}
      />
    </a>
  )
}

/**
 * Marca do Connect Academy — alvo com flecha, desenhada a partir do símbolo do logo
 * oficial. Vetorial e em `currentColor`, para ficar nítida a partir de 14px, onde a
 * versão em bitmap embaçaria. Um recorte (mask) abre o vão nos anéis por onde a
 * flecha passa, como no original.
 */
function ConnectMark({ className = 'h-3.5 w-3.5', ...props }) {
  const id = useId()
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
      focusable="false"
      {...props}
    >
      <mask id={id}>
        <rect width="24" height="24" fill="#fff" />
        <line x1="10.5" y1="13.5" x2="23" y2="1" stroke="#000" strokeWidth="5" strokeLinecap="round" />
      </mask>
      <g mask={`url(#${id})`}>
        <circle cx="10.5" cy="13.5" r="8.8" />
        <circle cx="10.5" cy="13.5" r="5" />
      </g>
      <circle cx="10.5" cy="13.5" r="1.9" fill="currentColor" />
      <path d="M10.5 13.5 L19.6 4.4" />
      <path d="M15.2 3.4 L20.6 3.4 L20.6 8.8" />
    </svg>
  )
}

/**
 * Símbolo 3D do Connect Academy com a flecha animada.
 *
 * A arte original vinha num arquivo só; a flecha foi separada do alvo em duas
 * camadas que se recompõem pixel a pixel — por isso o quadro final é idêntico à
 * imagem estática. Ao entrar em cena, a flecha vem do canto superior direito
 * (no eixo de 45° em que ela já está desenhada, dispensando rotação), o alvo dá
 * um coice no impacto e um anel dourado se expande.
 *
 * Quem pediu menos movimento no sistema recebe direto o quadro final.
 */
/**
 * Ciclo da animação, em segundos, e os instantes de cada etapa como fração dele.
 * A flecha volta ao ponto de partida recuando pelo mesmo eixo: como as seções
 * recortam o que passa das bordas, ela sai de quadro e o reinício não aparece —
 * por isso o laço dispensa qualquer fade.
 */
const CICLO = 4.4
const T_ACERTO = 0.75 / CICLO // flecha crava no alvo
const T_RECUO = 3.65 / CICLO // começa a recuar
const T_FORA = 3.97 / CICLO // já saiu de quadro; o resto do ciclo é pausa

function AnimatedTarget({ className = 'h-24', delay = 0, alt = 'Símbolo do Connect Academy' }) {
  const semMovimento = useReducedMotion()
  const ref = useRef(null)
  // O gatilho observa o container, não as camadas: a flecha começa fora da tela e
  // um whileInView nela própria nunca dispararia. Sem `once`, o laço só roda
  // enquanto o símbolo está à vista.
  const emCena = useInView(ref, { amount: 0.4 })

  const sombra = 'drop-shadow-[0_18px_45px_rgba(0,0,0,0.55)]'
  const estado = emCena ? 'acerto' : 'parado'
  const emLaco = { duration: CICLO, repeat: Infinity, delay }

  const alvoVar = {
    parado: { scale: 1 },
    acerto: {
      scale: [1, 1, 1.09, 0.97, 1, 1],
      transition: {
        ...emLaco,
        times: [0, T_ACERTO, T_ACERTO + 0.028, T_ACERTO + 0.06, T_ACERTO + 0.11, 1],
      },
    },
  }

  const anelVar = {
    parado: { scale: 0.25, opacity: 0 },
    acerto: {
      scale: [0.25, 0.25, 1, 1.75, 1.75],
      opacity: [0, 0, 0.8, 0, 0],
      transition: {
        ...emLaco,
        ease: 'easeOut',
        times: [0, T_ACERTO, T_ACERTO + 0.055, T_ACERTO + 0.15, 1],
      },
    },
  }

  const flechaVar = {
    parado: { x: '70vw', y: '-70vw' },
    acerto: {
      // voa até o alvo · fica cravada · recua para fora de quadro · pausa
      x: ['70vw', 0, 0, '70vw', '70vw'],
      y: ['-70vw', 0, 0, '-70vw', '-70vw'],
      transition: {
        ...emLaco,
        times: [0, T_ACERTO, T_RECUO, T_FORA, 1],
        ease: [[0.16, 0.86, 0.3, 1], 'linear', 'easeIn', 'linear'],
      },
    },
  }

  if (semMovimento) {
    return (
      <span className={`relative inline-block ${className}`}>
        <img src={targetAlvo} alt={alt} className={`h-full w-auto ${sombra}`} />
        <img src={targetFlecha} alt="" aria-hidden="true" className="absolute inset-0 h-full w-full" />
      </span>
    )
  }

  return (
    <span ref={ref} className={`relative inline-block ${className}`}>
      {/* Alvo — recua no impacto */}
      <motion.img
        src={targetAlvo}
        alt={alt}
        className={`h-full w-auto ${sombra}`}
        variants={alvoVar}
        initial="parado"
        animate={estado}
      />

      {/* Anel de impacto */}
      <motion.span
        aria-hidden="true"
        className="pointer-events-none absolute left-1/2 top-1/2 h-3/4 w-3/4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-[#F5CD55]"
        variants={anelVar}
        initial="parado"
        animate={estado}
      />

      {/* Flecha — entra pelo canto superior direito, no próprio eixo de 45° */}
      <motion.img
        src={targetFlecha}
        alt=""
        aria-hidden="true"
        className="absolute inset-0 h-full w-full"
        variants={flechaVar}
        initial="parado"
        animate={estado}
      />
    </span>
  )
}

function Badge({ children, className = '' }) {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border border-[#F5CD55]/40 bg-[#F5CD55]/10 px-4 py-1.5 text-[0.68rem] font-semibold uppercase tracking-[0.22em] text-[#F5CD55] backdrop-blur-sm sm:text-xs ${className}`}
    >
      {children}
    </span>
  )
}

function PrimaryButton({ href, children, className = '', ...props }) {
  return (
    <a
      href={href}
      className={`group inline-flex items-center justify-center gap-2.5 rounded-full bg-[#F5CD55] px-7 py-4 text-sm font-bold text-[#14193C] shadow-[0_18px_45px_-18px_rgba(245,205,85,0.95)] transition-all duration-300 hover:-translate-y-0.5 hover:bg-[#ffdd7a] hover:shadow-[0_22px_55px_-16px_rgba(245,205,85,1)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#F5CD55] focus-visible:ring-offset-2 focus-visible:ring-offset-[#14193C] sm:text-base ${className}`}
      {...props}
    >
      {children}
    </a>
  )
}

function GhostButton({ href, children, className = '' }) {
  return (
    <a
      href={href}
      className={`group inline-flex items-center justify-center gap-2.5 rounded-full border border-white/20 bg-white/[0.04] px-7 py-4 text-sm font-semibold text-white backdrop-blur-xl transition-all duration-300 hover:-translate-y-0.5 hover:border-[#F5CD55]/60 hover:text-[#F5CD55] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#F5CD55] focus-visible:ring-offset-2 focus-visible:ring-offset-[#14193C] sm:text-base ${className}`}
    >
      {children}
    </a>
  )
}

function SectionHeading({ eyebrow, title, highlight, description, center = true }) {
  return (
    <div className={`max-w-3xl ${center ? 'mx-auto text-center' : ''}`}>
      {eyebrow && (
        <Reveal>
          <Badge>
            <ConnectMark className="h-3.5 w-3.5" />
            {eyebrow}
          </Badge>
        </Reveal>
      )}
      <Reveal delay={0.08}>
        <h2 className="mt-6 text-3xl font-extrabold leading-tight tracking-tight text-white sm:text-4xl lg:text-[2.75rem]">
          {title} {highlight && <span className="gold-text animate-shine">{highlight}</span>}
        </h2>
      </Reveal>
      {description && (
        <Reveal delay={0.16}>
          <p className="mt-5 text-base leading-relaxed text-white/60 sm:text-lg">{description}</p>
        </Reveal>
      )}
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/*  Header / Navbar                                                            */
/* -------------------------------------------------------------------------- */

function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
    return () => {
      document.body.style.overflow = ''
    }
  }, [open])

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'border-b border-white/10 bg-[#14193C]/85 backdrop-blur-xl shadow-[0_10px_40px_-20px_rgba(0,0,0,0.9)]'
          : 'border-b border-transparent bg-transparent'
      }`}
    >
      <nav className="mx-auto flex h-20 max-w-7xl items-center justify-between px-5 sm:px-8">
        <Logo />

        <ul className="hidden items-center gap-9 lg:flex">
          {NAV_LINKS.map((link) => (
            <li key={link.href}>
              <a
                href={link.href}
                className="group relative text-sm font-medium text-white/70 transition-colors hover:text-white"
              >
                {link.label}
                <span className="absolute -bottom-1.5 left-0 h-px w-0 bg-[#F5CD55] transition-all duration-300 group-hover:w-full" />
              </a>
            </li>
          ))}
        </ul>

        <div className="flex items-center gap-3">
          <PrimaryButton
            href={WA_GERAL}
            target="_blank"
            rel="noopener noreferrer"
            className="hidden px-6 py-3 text-sm sm:inline-flex"
          >
            Garantir vaga
            <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
          </PrimaryButton>

          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-label={open ? 'Fechar menu' : 'Abrir menu'}
            aria-expanded={open}
            className="flex h-11 w-11 items-center justify-center rounded-full border border-white/15 bg-white/[0.04] text-white backdrop-blur-xl transition-colors hover:border-[#F5CD55]/50 hover:text-[#F5CD55] lg:hidden"
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </nav>

      {/* Menu mobile */}
      <div
        className={`overflow-hidden border-t border-white/10 bg-[#14193C]/95 backdrop-blur-xl transition-[max-height,opacity] duration-300 lg:hidden ${
          open ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <ul className="space-y-1 px-5 py-5 sm:px-8">
          {NAV_LINKS.map((link) => (
            <li key={link.href}>
              <a
                href={link.href}
                onClick={() => setOpen(false)}
                className="flex items-center justify-between rounded-2xl px-4 py-3.5 text-base font-medium text-white/80 transition-colors hover:bg-white/[0.05] hover:text-[#F5CD55]"
              >
                {link.label}
                <ArrowRight className="h-4 w-4 opacity-40" />
              </a>
            </li>
          ))}
          <li className="pt-3">
            <PrimaryButton
              href={WA_GERAL}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => setOpen(false)}
              className="w-full"
            >
              Garantir vaga
              <ArrowRight className="h-4 w-4" />
            </PrimaryButton>
          </li>
        </ul>
      </div>
    </header>
  )
}

/* -------------------------------------------------------------------------- */
/*  Hero                                                                       */
/* -------------------------------------------------------------------------- */

function useCountdown(targetDate) {
  const [restante, setRestante] = useState(() => new Date(targetDate).getTime() - Date.now())

  useEffect(() => {
    const alvo = new Date(targetDate).getTime()
    const id = setInterval(() => setRestante(alvo - Date.now()), 1000)
    return () => clearInterval(id)
  }, [targetDate])

  if (!(restante > 0)) return null

  const segundosTotais = Math.floor(restante / 1000)
  return {
    dias: Math.floor(segundosTotais / 86400),
    horas: Math.floor((segundosTotais % 86400) / 3600),
    minutos: Math.floor((segundosTotais % 3600) / 60),
    segundos: segundosTotais % 60,
  }
}

function ScarcityCard() {
  const countdown = useCountdown(EVENT_DATE)

  const blocos = countdown
    ? [
        { valor: countdown.dias, label: 'dias' },
        { valor: countdown.horas, label: 'horas' },
        { valor: countdown.minutos, label: 'min' },
        { valor: countdown.segundos, label: 'seg' },
      ]
    : []

  return (
    <div className="glass-gold relative overflow-hidden p-6 sm:p-7">
      <div className="pointer-events-none absolute -right-10 -top-10 h-36 w-36 rounded-full bg-[#F5CD55]/20 blur-3xl" />

      <div className="relative flex items-start gap-4">
        <span className="mt-0.5 flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[#F5CD55] text-[#14193C]">
          <Users className="h-5 w-5" strokeWidth={2.4} />
        </span>
        <div>
          <p className="text-base font-bold text-white sm:text-lg">Vagas limitadas</p>
          <p className="mt-1 text-sm leading-relaxed text-white/65">
            Apenas <span className="font-bold text-[#F5CD55]">{VAGAS_POR_TURMA} participantes</span>{' '}
            por turma — formato presencial e exclusivo.
          </p>
        </div>
      </div>

      {blocos.length > 0 && (
        <div className="relative mt-6 border-t border-[#F5CD55]/20 pt-5">
          <p className="mb-3 flex items-center gap-2 text-[0.65rem] font-semibold uppercase tracking-[0.22em] text-white/45">
            <Calendar className="h-3.5 w-3.5 text-[#F5CD55]" />
            Contagem para o pré-evento
          </p>
          <div className="grid grid-cols-4 gap-2.5">
            {blocos.map((b) => (
              <div
                key={b.label}
                className="rounded-2xl border border-white/10 bg-[#14193C]/60 py-3 text-center backdrop-blur-sm"
              >
                <span className="block text-xl font-extrabold tabular-nums text-[#F5CD55] sm:text-2xl">
                  {String(b.valor).padStart(2, '0')}
                </span>
                <span className="mt-0.5 block text-[0.6rem] uppercase tracking-widest text-white/45">
                  {b.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function Hero() {
  return (
    <section id="topo" className="relative overflow-hidden pb-24 pt-32 sm:pb-28 sm:pt-40 lg:pt-44">
      {/* Fundo: degradês suaves navy + halos dourados */}
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute inset-0 bg-[radial-gradient(120%_90%_at_50%_-10%,#1d2455_0%,#14193C_45%,#0D1129_100%)]" />
        <div className="absolute -left-40 top-24 h-[26rem] w-[26rem] rounded-full bg-[#F5CD55]/10 blur-[130px]" />
        <div className="absolute -right-32 top-1/3 h-[30rem] w-[30rem] rounded-full bg-[#F5CD55]/[0.07] blur-[150px]" />
        <div
          className="absolute inset-0 opacity-[0.35]"
          style={{
            backgroundImage:
              'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)',
            backgroundSize: '64px 64px',
            maskImage: 'radial-gradient(70% 55% at 50% 40%, #000 0%, transparent 100%)',
            WebkitMaskImage: 'radial-gradient(70% 55% at 50% 40%, #000 0%, transparent 100%)',
          }}
        />
      </div>

      <div className="mx-auto grid max-w-7xl items-center gap-14 px-5 sm:px-8 lg:grid-cols-[1.15fr_0.85fr] lg:gap-16">
        {/* Coluna de texto */}
        <div>
          <Reveal>
            <Badge>
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-pulse-ring rounded-full bg-[#F5CD55]" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-[#F5CD55]" />
              </span>
              Pré-evento 18 fev · Imersão 19 e 20 fev — apenas {VAGAS_POR_TURMA} vagas
            </Badge>
          </Reveal>

          <Reveal delay={0.1}>
            <h1 className="mt-7 text-[2.6rem] font-extrabold leading-[1.05] tracking-tight text-white sm:text-6xl lg:text-[4.25rem]">
              Gestão. Pessoas.
              <br />
              <span className="gold-text animate-shine">Crescimento. Futuro.</span>
            </h1>
          </Reveal>

          <Reveal delay={0.18}>
            <p className="mt-7 max-w-xl text-base leading-relaxed text-white/65 sm:text-lg">
              Conectamos conhecimento, prática e estratégia para formar líderes mais preparados e
              empresas mais fortes.{' '}
              <span className="font-medium text-white">
                Escolha a imersão ideal para o seu momento.
              </span>
            </p>
          </Reveal>

          <Reveal delay={0.26}>
            <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:items-center">
              <PrimaryButton href={WA_GERAL} target="_blank" rel="noopener noreferrer">
                <MessageCircle className="h-5 w-5" strokeWidth={2.4} />
                Fale com a nossa equipe
              </PrimaryButton>
              <GhostButton href="#imersoes">
                Ver trilhas de imersão
                <ChevronDown className="h-4 w-4 transition-transform duration-300 group-hover:translate-y-0.5" />
              </GhostButton>
            </div>
          </Reveal>

          <Reveal delay={0.34}>
            <dl className="mt-12 grid max-w-lg grid-cols-3 gap-4 border-t border-white/10 pt-8">
              {[
                { valor: '06', label: 'trilhas de imersão' },
                { valor: '20', label: 'vagas por turma' },
                { valor: '100%', label: 'presencial e prático' },
              ].map((item) => (
                <div key={item.label}>
                  <dt className="text-2xl font-extrabold text-[#F5CD55] sm:text-3xl">
                    {item.valor}
                  </dt>
                  <dd className="mt-1 text-[0.7rem] uppercase leading-snug tracking-wider text-white/45 sm:text-xs">
                    {item.label}
                  </dd>
                </div>
              ))}
            </dl>
          </Reveal>
        </div>

        {/* Coluna visual */}
        <Reveal delay={0.2}>
          <div className="relative">
            <div className="pointer-events-none absolute -inset-8 -z-10 rounded-full bg-[#F5CD55]/10 blur-[90px]" />

            <div className="glass relative overflow-hidden p-8 sm:p-10">
              <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#F5CD55]/60 to-transparent" />

              <div className="relative flex justify-center">
                {/* Halo dourado para o alvo 3D destacar-se do navy */}
                <div className="pointer-events-none absolute left-1/2 top-1/2 h-48 w-48 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#F5CD55]/25 blur-[55px] sm:h-56 sm:w-56" />
                <span className="relative animate-float">
                  <AnimatedTarget className="h-36 sm:h-44" delay={0.35} />
                </span>
              </div>

              <p className="mt-8 text-center text-xl font-bold leading-snug text-white sm:text-2xl">
                Sua empresa está pronta para o{' '}
                <span className="text-[#F5CD55]">próximo nível?</span>
              </p>

              <div className="mt-8 space-y-3">
                {[
                  { icon: Calendar, texto: 'Pré-evento: 18 de fevereiro' },
                  { icon: Calendar, texto: 'Imersão: 19 e 20 de fevereiro' },
                  { icon: MapPin, texto: 'Presencial e exclusiva' },
                ].map((item) => (
                  <div
                    key={item.texto}
                    className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 backdrop-blur-sm"
                  >
                    <item.icon className="h-4 w-4 shrink-0 text-[#F5CD55]" />
                    <span className="text-sm font-medium text-white/80">{item.texto}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-5">
              <ScarcityCard />
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  )
}

/* -------------------------------------------------------------------------- */
/*  Sobre                                                                      */
/* -------------------------------------------------------------------------- */

function About() {
  return (
    <section
      id="sobre"
      className="relative overflow-hidden border-t border-white/[0.06] py-24 sm:py-28"
    >
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[linear-gradient(180deg,#14193C_0%,#161C46_50%,#14193C_100%)]" />

      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <div className="grid items-center gap-14 lg:grid-cols-2 lg:gap-20">
          <div>
            <SectionHeading
              center={false}
              eyebrow="O que é o Connect Academy"
              title="A escola de negócios do"
              highlight="ecossistema Connect Valley"
              description="Por meio de imersões práticas, preparamos empresários, gestores, líderes e equipes para enfrentar desafios reais de gestão, estratégia, pessoas, tecnologia e crescimento."
            />

            <Reveal delay={0.24}>
              <div className="glass-gold mt-10 p-7 sm:p-8">
                <p className="text-lg font-bold leading-snug text-white sm:text-xl">
                  Aqui, conhecimento se transforma em{' '}
                  <span className="gold-text animate-shine">
                    método, decisões melhores e resultados sustentáveis.
                  </span>
                </p>
              </div>
            </Reveal>

            <Reveal delay={0.32}>
              <div className="mt-8">
                <PrimaryButton href={WA_GERAL} target="_blank" rel="noopener noreferrer">
                  Conheça as próximas turmas
                  <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
                </PrimaryButton>
              </div>
            </Reveal>
          </div>

          <div className="space-y-5">
            <Reveal>
              <figure className="glass relative overflow-hidden">
                <img
                  src={fotoEvento2}
                  alt="Participantes durante uma imersão presencial do Connect Academy"
                  className="h-56 w-full object-cover sm:h-64"
                />
                <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-[#14193C] via-[#14193C]/30 to-transparent" />
                <figcaption className="absolute inset-x-0 bottom-0 p-6 text-sm font-semibold leading-snug text-white">
                  Turmas reduzidas, troca real entre quem decide.
                </figcaption>
              </figure>
            </Reveal>

            <div className="grid gap-5 sm:grid-cols-2">
            {[
              {
                icon: Briefcase,
                titulo: 'Para quem decide',
                texto: 'Empresários, gestores, líderes e equipes que precisam de resultado.',
              },
              {
                icon: Layers,
                titulo: 'Desafios reais',
                texto: 'Gestão, estratégia, pessoas, tecnologia e crescimento na prática.',
              },
              {
                icon: Compass,
                titulo: 'Método antes de teoria',
                texto: 'Conteúdo aplicável, transformado em rotina e processo na sua empresa.',
              },
              {
                icon: TrendingUp,
                titulo: 'Resultado sustentável',
                texto: 'Decisões melhores hoje, base sólida para crescer com previsibilidade.',
              },
            ].map((item, i) => (
              <Reveal key={item.titulo} delay={0.1 + i * 0.08}>
                <div className="glass group h-full p-6 transition-all duration-300 hover:-translate-y-1 hover:border-[#F5CD55]/35">
                  <span className="flex h-11 w-11 items-center justify-center rounded-2xl border border-[#F5CD55]/25 bg-[#F5CD55]/10 text-[#F5CD55] transition-colors duration-300 group-hover:bg-[#F5CD55] group-hover:text-[#14193C]">
                    <item.icon className="h-5 w-5" strokeWidth={2.2} />
                  </span>
                  <h3 className="mt-5 text-base font-bold text-white">{item.titulo}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-white/55">{item.texto}</p>
                </div>
              </Reveal>
            ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

/* -------------------------------------------------------------------------- */
/*  Trilhas / Imersões                                                         */
/* -------------------------------------------------------------------------- */

/**
 * Bloco de destaque do Connect Med — largura total, tratamento cinematográfico e a
 * foto da dupla que abre o folder impresso. Fica fora da grade das demais trilhas
 * justamente para não competir com elas.
 */
function FeaturedMed({ track }) {
  return (
    <Reveal>
      <article
        id={track.id}
        className="relative overflow-hidden rounded-[2rem] border border-[#F5CD55]/35 bg-[linear-gradient(125deg,#0B1130_0%,#14193C_42%,#1B2A63_100%)] shadow-[0_40px_90px_-40px_rgba(0,0,0,0.9)]"
      >
        {/* Feixes de luz azul e halo dourado, como na capa do folder */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -left-24 top-0 h-72 w-72 rounded-full bg-[#2C57C4]/25 blur-[110px]" />
          <div className="absolute bottom-0 right-1/3 h-80 w-80 rounded-full bg-[#F5CD55]/10 blur-[120px]" />
          <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#F5CD55]/60 to-transparent" />
        </div>

        <div className="relative grid lg:grid-cols-[1.04fr_0.96fr]">
          {/* Conteúdo */}
          <div className="p-8 sm:p-11 lg:p-14">
            <span className="inline-flex items-center gap-2 rounded-full bg-[#F5CD55] px-4 py-1.5 text-[0.6rem] font-extrabold uppercase tracking-[0.2em] text-[#14193C]">
              <ConnectMark className="h-3.5 w-3.5" />
              Imersão em destaque
            </span>

            <img
              src={track.lockup}
              alt={track.nome}
              className="mt-7 h-20 w-auto drop-shadow-[0_14px_40px_rgba(0,0,0,0.6)] sm:h-24 lg:h-28"
            />
            <h3 className="sr-only">{track.nome}</h3>

            <p className="mt-5 text-base font-semibold text-[#F5CD55] sm:text-lg">
              {track.chamada}
            </p>

            <p className="mt-5 max-w-xl text-sm leading-relaxed text-white/65 sm:text-base">
              {track.descricao}
            </p>

            {/* Os três eixos do programa, no formato de selo da capa do folder */}
            <ul className="mt-7 flex flex-wrap gap-2.5">
              {track.eixos.map((eixo) => (
                <li
                  key={eixo}
                  className="rounded-xl border border-[#5B8BD0]/40 bg-gradient-to-b from-[#1B2A63]/80 to-[#111a45]/80 px-4 py-2.5 text-xs font-bold uppercase tracking-wider text-white shadow-[inset_0_1px_0_0_rgba(255,255,255,0.12)] sm:text-[0.8rem]"
                >
                  {eixo}
                </li>
              ))}
            </ul>

            <div className="mt-8 flex flex-wrap items-center gap-x-8 gap-y-4 border-t border-white/10 pt-7">
              <div>
                <p className="text-[0.6rem] font-semibold uppercase tracking-[0.22em] text-white/45">
                  Pré-evento
                </p>
                <p className="mt-1 text-xl font-extrabold text-white">18 FEV</p>
              </div>
              <div>
                <p className="text-[0.6rem] font-semibold uppercase tracking-[0.22em] text-white/45">
                  Imersão
                </p>
                <p className="mt-1 text-xl font-extrabold text-white">19 E 20 FEV</p>
              </div>
              <img
                src={selo20Vagas}
                alt="Apenas 20 vagas"
                className="h-14 w-auto drop-shadow-[0_10px_26px_rgba(245,205,85,0.35)] sm:h-16"
              />
            </div>

            <p className="mt-7 rounded-2xl border-l-2 border-[#F5CD55] bg-[#F5CD55]/[0.07] px-5 py-4 text-sm font-semibold italic leading-snug text-white sm:text-base">
              “{track.slogan}”
            </p>

            <PrimaryButton
              href={waLink(
                `Olá! Tenho interesse na imersão ${track.nome} do Connect Academy. Pode me enviar mais informações?`,
              )}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-7"
            >
              <MessageCircle className="h-5 w-5" strokeWidth={2.4} />
              Quero o Connect Med
            </PrimaryButton>
          </div>

          {/* Foto — encosta na base do bloco, como no folder */}
          <div className="relative min-h-[380px] sm:min-h-[440px] lg:min-h-0">
            {/* object-contain mantém a foto dentro da própria coluna, sem invadir o texto */}
            <img
              src={fotoEquipeMed}
              alt="Especialistas que conduzem a imersão Connect Med"
              className="absolute inset-0 h-full w-full object-contain object-bottom lg:object-right-bottom"
            />
          </div>
        </div>
      </article>
    </Reveal>
  )
}

function TrackCard({ track, index }) {
  const Icon = track.icon
  const largo = Boolean(track.wide)

  return (
    <Reveal delay={Math.min(index, 3) * 0.08} className={largo ? 'md:col-span-2' : ''}>
      <article
        id={track.id}
        className="glass group relative flex h-full flex-col overflow-hidden p-7 transition-all duration-300 hover:-translate-y-1.5 hover:border-[#F5CD55]/35 sm:p-8"
      >
        <div className="pointer-events-none absolute -right-16 -top-16 h-40 w-40 rounded-full bg-[#F5CD55]/10 blur-3xl transition-opacity duration-500 group-hover:opacity-100 sm:opacity-0" />

        <div className="relative flex items-center gap-4">
          {track.badge ? (
            /* Badge circular oficial da trilha */
            <img
              src={track.badge}
              alt=""
              aria-hidden="true"
              className="h-16 w-16 shrink-0 rounded-full ring-1 ring-[#F5CD55]/25 transition-all duration-300 group-hover:ring-[#F5CD55]/70"
            />
          ) : (
            <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border border-[#F5CD55]/25 bg-[#F5CD55]/10 text-[#F5CD55] transition-all duration-300 group-hover:bg-[#F5CD55] group-hover:text-[#14193C]">
              <Icon className="h-7 w-7" strokeWidth={2} />
            </span>
          )}
          <div className="min-w-0">
            <h3 className="text-xl font-extrabold leading-tight text-white sm:text-2xl">
              {track.nome}
            </h3>
            <p className="mt-1 text-sm font-medium text-[#F5CD55]">{track.chamada}</p>
          </div>
        </div>

        <p className="relative mt-6 text-sm leading-relaxed text-white/60">{track.descricao}</p>

        <ul
          className={`relative mt-6 grid gap-2.5 ${largo ? 'sm:grid-cols-2' : ''}`}
          aria-label={`O que você aprende no ${track.nome}`}
        >
          {track.topicos.map((topico) => (
            <li key={topico} className="flex items-start gap-2.5">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-[#F5CD55]" strokeWidth={2.4} />
              <span className="text-sm leading-snug text-white/75">{topico}</span>
            </li>
          ))}
        </ul>

        <div className="relative mt-auto pt-7">
          <p className="rounded-2xl border-l-2 border-[#F5CD55] bg-[#F5CD55]/[0.07] px-5 py-4 text-sm font-semibold italic leading-snug text-white">
            “{track.slogan}”
          </p>

          <a
            href={waLink(
              `Olá! Tenho interesse na imersão ${track.nome} do Connect Academy. Pode me enviar mais informações?`,
            )}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-5 inline-flex items-center gap-2 text-sm font-bold text-[#F5CD55] transition-colors hover:text-white"
          >
            Quero esta imersão
            <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
          </a>
        </div>
      </article>
    </Reveal>
  )
}

function Tracks() {
  return (
    <section
      id="imersoes"
      className="relative overflow-hidden border-t border-white/[0.06] py-24 sm:py-28"
    >
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[#14193C]">
        <div className="absolute left-1/2 top-0 h-96 w-[42rem] -translate-x-1/2 rounded-full bg-[#F5CD55]/[0.06] blur-[140px]" />
      </div>

      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <SectionHeading
          eyebrow="Trilhas de imersão"
          title="Escolha a imersão ideal"
          highlight="para o seu momento"
          description="Seis trilhas construídas para resolver problemas reais de gestão. Todas presenciais, práticas e com turmas de no máximo 20 participantes."
        />

        <div className="mt-14">
          <FeaturedMed track={TRACKS.find((t) => t.destaque)} />
        </div>

        <p className="mt-14 text-center text-[0.65rem] font-semibold uppercase tracking-[0.24em] text-white/35">
          As demais trilhas
        </p>

        <div className="mt-6 grid gap-6 md:grid-cols-2">
          {TRACKS.filter((t) => !t.destaque).map((track, i) => (
            <TrackCard key={track.id} track={track} index={i} />
          ))}
        </div>

        <Reveal delay={0.1}>
          <p className="mt-12 text-center text-sm text-white/45">
            Não sabe qual trilha escolher?{' '}
            <a
              href={waLink(
                'Olá! Não sei qual trilha do Connect Academy é a ideal para o meu momento. Podem me ajudar?',
              )}
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold text-[#F5CD55] underline decoration-[#F5CD55]/40 underline-offset-4 transition-colors hover:text-white"
            >
              Fale com a nossa equipe
            </a>{' '}
            e receba uma recomendação.
          </p>
        </Reveal>
      </div>
    </section>
  )
}

/* -------------------------------------------------------------------------- */
/*  Diferenciais                                                               */
/* -------------------------------------------------------------------------- */

function Why() {
  return (
    <section
      id="diferenciais"
      className="relative overflow-hidden border-t border-white/[0.06] py-24 sm:py-28"
    >
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[linear-gradient(180deg,#14193C_0%,#171D48_50%,#14193C_100%)]" />

      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <SectionHeading
          eyebrow="Por que participar"
          title="Uma imersão feita para"
          highlight="mudar a sua operação"
          description="O Connect Academy não entrega mais um curso. Entrega método, contexto e rede — os três ativos que separam quem aprende de quem executa."
        />

        <div className="mt-14 grid gap-6 md:grid-cols-3">
          {DIFERENCIAIS.map((item, i) => (
            <Reveal key={item.titulo} delay={i * 0.1}>
              <div className="glass group relative h-full overflow-hidden p-8 transition-all duration-300 hover:-translate-y-1.5 hover:border-[#F5CD55]/35">
                <span className="absolute right-6 top-6 text-5xl font-extrabold text-white/[0.04] transition-colors duration-300 group-hover:text-[#F5CD55]/10">
                  0{i + 1}
                </span>
                <span className="flex h-14 w-14 items-center justify-center rounded-2xl border border-[#F5CD55]/25 bg-[#F5CD55]/10 text-[#F5CD55] transition-colors duration-300 group-hover:bg-[#F5CD55] group-hover:text-[#14193C]">
                  <item.icon className="h-7 w-7" strokeWidth={2} />
                </span>
                <h3 className="mt-6 text-lg font-extrabold leading-snug text-white sm:text-xl">
                  {item.titulo}
                </h3>
                <p className="mt-3 text-sm leading-relaxed text-white/60">{item.texto}</p>
              </div>
            </Reveal>
          ))}
        </div>

        {/* Faixa de datas */}
        <Reveal delay={0.2}>
          <div className="glass-gold relative mt-12 overflow-hidden p-8 text-center sm:p-10 lg:text-left">
            {/* Foto de uma imersão real, sob véu navy para preservar o contraste do texto */}
            <div className="pointer-events-none absolute inset-0">
              <img
                src={fotoEvento1}
                alt=""
                aria-hidden="true"
                className="h-full w-full object-cover object-center"
              />
              <div className="absolute inset-0 bg-gradient-to-r from-[#14193C] via-[#14193C]/85 to-[#14193C]/45" />
            </div>

            <div className="relative flex flex-col items-center justify-between gap-6 lg:flex-row lg:text-left">
            <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-center">
              <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-[#F5CD55] text-[#14193C]">
                <Calendar className="h-7 w-7" strokeWidth={2.2} />
              </span>
              <div>
                <p className="text-[0.65rem] font-semibold uppercase tracking-[0.24em] text-[#F5CD55]">
                  Presencial e exclusiva
                </p>
                <p className="mt-2 text-xl font-extrabold text-white sm:text-2xl">
                  Pré-evento 18 fev · Imersão 19 e 20 fev
                </p>
                <p className="mt-1 text-sm text-white/55">
                  Apenas {VAGAS_POR_TURMA} participantes por turma.
                </p>
              </div>
            </div>

            <PrimaryButton
              href={WA_GERAL}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full shrink-0 lg:w-auto"
            >
              Garantir vaga
              <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
            </PrimaryButton>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  )
}

/* -------------------------------------------------------------------------- */
/*  CTA final + Footer                                                         */
/* -------------------------------------------------------------------------- */

function FinalCTA() {
  return (
    <section id="contato" className="relative overflow-hidden py-24 sm:py-32">
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute inset-0 bg-[radial-gradient(90%_80%_at_50%_100%,#1d2455_0%,#14193C_55%,#0D1129_100%)]" />
        <div className="absolute bottom-0 left-1/2 h-96 w-[46rem] -translate-x-1/2 rounded-full bg-[#F5CD55]/10 blur-[130px]" />
      </div>

      <div className="mx-auto max-w-4xl px-5 text-center sm:px-8">
        <Reveal>
          <div className="relative mx-auto w-fit">
            <div className="pointer-events-none absolute left-1/2 top-1/2 h-36 w-36 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#F5CD55]/25 blur-[50px]" />
            <span className="relative block animate-float">
              <AnimatedTarget className="h-24 sm:h-28" />
            </span>
          </div>
        </Reveal>

        <Reveal delay={0.1}>
          <h2 className="mt-9 text-3xl font-extrabold leading-tight tracking-tight text-white sm:text-5xl">
            Sua empresa está pronta para o{' '}
            <span className="gold-text animate-shine">próximo nível?</span>
          </h2>
        </Reveal>

        <Reveal delay={0.18}>
          <p className="mx-auto mt-6 max-w-2xl text-base leading-relaxed text-white/65 sm:text-lg">
            Fale com a nossa equipe, conheça as próximas turmas e garanta uma das{' '}
            <span className="font-semibold text-[#F5CD55]">{VAGAS_POR_TURMA} vagas</span> da imersão
            que faz sentido para o seu momento.
          </p>
        </Reveal>

        <Reveal delay={0.26}>
          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <PrimaryButton href={WA_GERAL} target="_blank" rel="noopener noreferrer">
              <MessageCircle className="h-5 w-5" strokeWidth={2.4} />
              Falar no WhatsApp · {WHATSAPP_DISPLAY}
            </PrimaryButton>
            <GhostButton href={INSTAGRAM_URL}>
              <Instagram className="h-5 w-5" />@{INSTAGRAM_HANDLE}
            </GhostButton>
          </div>
        </Reveal>

        <Reveal delay={0.34}>
          <p className="mt-8 text-xs uppercase tracking-[0.24em] text-white/35">
            Resposta rápida · Turmas em formação
          </p>
        </Reveal>
      </div>
    </section>
  )
}

function Footer() {
  const ano = new Date().getFullYear()

  return (
    <footer className="border-t border-white/10 bg-[#0D1129]">
      <div className="mx-auto max-w-7xl px-5 py-14 sm:px-8">
        <div className="grid gap-10 md:grid-cols-[1.4fr_1fr_1fr]">
          <div>
            <Logo />
            <p className="mt-5 max-w-sm text-sm leading-relaxed text-[#727272]">
              A escola de negócios e inteligência corporativa do ecossistema Connect Valley.
              Imersões práticas para empresários, gestores, líderes e equipes.
            </p>
          </div>

          <nav aria-label="Navegação do rodapé">
            <h3 className="text-xs font-semibold uppercase tracking-[0.22em] text-[#F5CD55]">
              Navegação
            </h3>
            <ul className="mt-5 space-y-3">
              {NAV_LINKS.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="text-sm text-white/60 transition-colors hover:text-[#F5CD55]"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>

          <div>
            <h3 className="text-xs font-semibold uppercase tracking-[0.22em] text-[#F5CD55]">
              Contato
            </h3>
            <ul className="mt-5 space-y-3">
              <li>
                <a
                  href={WA_GERAL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2.5 text-sm text-white/60 transition-colors hover:text-[#F5CD55]"
                >
                  <MessageCircle className="h-4 w-4 text-[#F5CD55]" />
                  {WHATSAPP_DISPLAY}
                </a>
              </li>
              <li>
                <a
                  href={INSTAGRAM_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2.5 text-sm text-white/60 transition-colors hover:text-[#F5CD55]"
                >
                  <Instagram className="h-4 w-4 text-[#F5CD55]" />@{INSTAGRAM_HANDLE}
                </a>
              </li>
              <li className="inline-flex items-center gap-2.5 text-sm text-white/60">
                <Calendar className="h-4 w-4 text-[#F5CD55]" />
                Pré-evento 18 fev · Imersão 19 e 20 fev
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-white/10 pt-8 text-center sm:flex-row sm:text-left">
          <p className="text-xs text-[#727272]">
            © {ano} Connect Academy® · Connect Valley. Todos os direitos reservados.
          </p>
          <p className="text-xs text-[#727272]">Gestão. Pessoas. Crescimento. Futuro.</p>
        </div>
      </div>
    </footer>
  )
}

function FloatingWhatsApp() {
  return (
    <a
      href={WA_GERAL}
      target="_blank"
      rel="noopener noreferrer"
      aria-label="Falar com a equipe do Connect Academy no WhatsApp"
      className="group fixed bottom-6 right-5 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-[#F5CD55] text-[#14193C] shadow-[0_16px_40px_-12px_rgba(245,205,85,0.9)] transition-transform duration-300 hover:scale-110 sm:bottom-8 sm:right-8"
    >
      <span className="absolute inset-0 animate-pulse-ring rounded-full bg-[#F5CD55]" />
      <MessageCircle className="relative h-6 w-6" strokeWidth={2.4} />
    </a>
  )
}

/* -------------------------------------------------------------------------- */
/*  Página                                                                     */
/* -------------------------------------------------------------------------- */

export default function ConnectAcademyLanding() {
  return (
    <div className="min-h-screen overflow-x-clip bg-[#14193C] font-sans text-white">
      <Navbar />
      <main>
        <Hero />
        <About />
        <Tracks />
        <Why />
        <FinalCTA />
      </main>
      <Footer />
      <FloatingWhatsApp />
    </div>
  )
}
