import { ThemeProvider, createTheme, CssBaseline, Box } from '@mui/material';
import Header from './components/Header';
import Hero from './components/Hero';
import Services from './components/Services';
import About from './components/About';
import Contact from './components/Contact';
import Footer from './components/Footer';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00D4FF',
    },
    secondary: {
      main: '#7B2FFF',
    },
    background: {
      default: '#0a0f1e',
      paper: '#1a1a2e',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
});

function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        background: 'linear-gradient(135deg, #0a0f1e 0%, #1a1a2e 100%)',
      }}>
        <Header />
        <Hero />
        <Services />
        <About />
        <Contact />
        <Footer />
      </Box>
    </ThemeProvider>
  );
}

export default App;
