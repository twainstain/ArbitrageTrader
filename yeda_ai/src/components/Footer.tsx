import { Box, Container, Link, Typography, Grid } from '@mui/material';
import EmailIcon from '@mui/icons-material/Email';
import PhoneIcon from '@mui/icons-material/Phone';

const Footer = () => {
  const links = [
    { text: 'Home', href: '#home' },
    { text: 'Services', href: '#services' },
    { text: 'About', href: '#about' },
    { text: 'Contact', href: '#contact' },
  ];

  return (
    <Box component="footer" sx={{
      py: 4,
      backgroundColor: 'rgba(8, 15, 28, 0.98)',
      borderTop: '1px solid rgba(100, 180, 255, 0.1)',
      mt: 'auto',
    }}>
      <Container maxWidth="lg">
        <Grid container spacing={4}>
          <Grid size={{ xs: 12, md: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Box sx={{
                width: 48, height: 48,
                background: 'linear-gradient(135deg, #1E3A5F 0%, #0F2439 100%)',
                borderRadius: '12px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 15px rgba(59, 130, 246, 0.2)',
                border: '1px solid rgba(100, 180, 255, 0.25)',
              }}>
                {/* Y-shaped connected dots icon */}
                <svg width="20" height="16" viewBox="0 0 20 16" style={{ marginBottom: 1 }}>
                  <line x1="4" y1="3" x2="10" y2="9" stroke="#64B4FF" strokeWidth="1.5" strokeLinecap="round"/>
                  <line x1="16" y1="3" x2="10" y2="9" stroke="#64B4FF" strokeWidth="1.5" strokeLinecap="round"/>
                  <line x1="10" y1="9" x2="10" y2="15" stroke="#64B4FF" strokeWidth="1.5" strokeLinecap="round"/>
                  <circle cx="4" cy="3" r="2" fill="#64B4FF"/>
                  <circle cx="16" cy="3" r="2" fill="#64B4FF"/>
                  <circle cx="10" cy="9" r="2.5" fill="#3B82F6"/>
                  <circle cx="10" cy="15" r="2" fill="#64B4FF"/>
                </svg>
                <Typography sx={{
                  background: 'linear-gradient(135deg, #64B4FF, #3B82F6)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  fontWeight: 700,
                  fontSize: '0.55rem',
                  lineHeight: 1,
                  letterSpacing: '0.5px',
                }}>
                  AI
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 0.8 }}>
                <Typography variant="h5" sx={{
                  fontWeight: 700,
                  background: 'linear-gradient(135deg, #FFFFFF 0%, #E2E8F0 50%, #CBD5E1 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  fontSize: '1.5rem',
                  letterSpacing: '-0.5px',
                }}>
                  Yeda
                </Typography>
                <Typography sx={{
                  fontWeight: 600,
                  background: 'linear-gradient(135deg, #64B4FF 0%, #3B82F6 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  fontSize: '1.1rem',
                  letterSpacing: '1px',
                }}>
                  AI
                </Typography>
              </Box>
            </Box>
            <Typography variant="body2" sx={{ color: 'rgba(226,232,240,0.5)', maxWidth: 280, fontSize: '0.875rem' }}>
              Transforming businesses with cutting-edge software, data analytics, and AI solutions.
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Typography variant="h6" sx={{ color: '#E2E8F0', mb: 2, fontWeight: 600, fontSize: '1rem' }}>Quick Links</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {links.map((link) => (
                <Link key={link.text} href={link.href} sx={{
                  color: 'rgba(226,232,240,0.6)',
                  textDecoration: 'none',
                  transition: 'color 0.3s',
                  fontSize: '0.875rem',
                  '&:hover': { color: '#64B4FF' },
                }}>
                  {link.text}
                </Link>
              ))}
            </Box>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Typography variant="h6" sx={{ color: '#E2E8F0', mb: 2, fontWeight: 600, fontSize: '1rem' }}>Contact Us</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              <Box sx={{
                color: 'rgba(226,232,240,0.6)',
                display: 'flex', alignItems: 'center', gap: 1,
                cursor: 'pointer',
                transition: 'color 0.3s',
                fontSize: '0.875rem',
                '&:hover': { color: '#64B4FF' },
              }}
              onClick={() => document.getElementById('contact')?.scrollIntoView({ behavior: 'smooth' })}
              >
                <EmailIcon fontSize="small" /> Send us a message
              </Box>
              <Link href="tel:+1234567890" sx={{
                color: 'rgba(226,232,240,0.6)',
                textDecoration: 'none',
                display: 'flex', alignItems: 'center', gap: 1,
                fontSize: '0.875rem',
                '&:hover': { color: '#64B4FF' },
              }}>
                <PhoneIcon fontSize="small" /> +1 (234) 567-890
              </Link>
            </Box>
          </Grid>
        </Grid>
        <Box sx={{ borderTop: '1px solid rgba(100,180,255,0.1)', mt: 4, pt: 3 }}>
          <Typography variant="body2" align="center" sx={{ color: 'rgba(226,232,240,0.4)', fontSize: '0.8rem' }}>
            © {new Date().getFullYear()} Yeda AI. All rights reserved.
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default Footer;

