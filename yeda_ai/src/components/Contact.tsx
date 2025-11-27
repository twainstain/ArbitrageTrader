import { Box, Container, Typography, Grid, Card, CardContent, Button, TextField } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import PhoneIcon from '@mui/icons-material/Phone';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';

const inputStyle = {
  '& .MuiOutlinedInput-root': {
    color: '#E2E8F0',
    '& fieldset': { borderColor: 'rgba(100, 180, 255, 0.2)' },
    '&:hover fieldset': { borderColor: 'rgba(100, 180, 255, 0.4)' },
    '&.Mui-focused fieldset': { borderColor: '#64B4FF' },
  },
  '& .MuiInputLabel-root': { color: 'rgba(226,232,240,0.6)' },
  '& .MuiInputLabel-root.Mui-focused': { color: '#64B4FF' },
};

const contactInfo = [
  { icon: <SendIcon sx={{ fontSize: 36 }} />, title: 'Send Message', info: 'Use the form to reach us', href: '#contact-form' },
  { icon: <PhoneIcon sx={{ fontSize: 36 }} />, title: 'Call Us', info: '+1 (234) 567-890', href: 'tel:+1234567890' },
  { icon: <CalendarMonthIcon sx={{ fontSize: 36 }} />, title: 'Schedule a Meeting', info: 'Book a time with our team', href: 'https://calendly.com', target: '_blank' },
];

// Hidden email for form submission
const CONTACT_EMAIL = 'yeda.al.sales@gmail.com';

const Contact = () => {
  return (
    <Box id="contact" sx={{ py: 12, background: 'linear-gradient(180deg, #132238 0%, #0B1426 100%)' }}>
      <Container maxWidth="lg">
        <Box sx={{ textAlign: 'center', mb: 8 }}>
          <Typography variant="overline" sx={{ color: '#64B4FF', letterSpacing: 3, fontWeight: 500 }}>Get in Touch</Typography>
          <Typography variant="h2" sx={{ fontSize: { xs: '2rem', md: '2.75rem' }, fontWeight: 600, color: '#E2E8F0', mt: 1, letterSpacing: '-0.5px' }}>
            Contact Us
          </Typography>
          <Typography sx={{ color: 'rgba(226,232,240,0.6)', mt: 2, maxWidth: 600, mx: 'auto' }}>
            Ready to transform your business? Reach out to us and let's discuss how we can help.
          </Typography>
        </Box>
        <Grid container spacing={4}>
          <Grid size={{ xs: 12, md: 5 }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              {contactInfo.map((item) => (
                <Card
                  key={item.title}
                  component="a"
                  href={item.href}
                  target={'target' in item ? item.target : undefined}
                  rel={'target' in item ? 'noopener noreferrer' : undefined}
                  sx={{
                    background: 'rgba(19, 34, 56, 0.8)',
                    border: '1px solid rgba(100, 180, 255, 0.15)',
                    borderRadius: 2,
                    textDecoration: 'none',
                    transition: 'all 0.3s ease',
                    '&:hover': { borderColor: 'rgba(100, 180, 255, 0.3)', transform: 'translateX(5px)', boxShadow: '0 4px 20px rgba(11, 20, 38, 0.5)' },
                  }}
                >
                  <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 3, p: 3 }}>
                    <Box sx={{
                      width: 60, height: 60, borderRadius: '12px',
                      background: 'linear-gradient(135deg, rgba(59,130,246,0.15), rgba(100,180,255,0.1))',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      color: '#64B4FF',
                    }}>
                      {item.icon}
                    </Box>
                    <Box>
                      <Typography variant="h6" sx={{ color: '#E2E8F0', fontWeight: 600, fontSize: '1rem' }}>{item.title}</Typography>
                      <Typography sx={{ color: 'rgba(226,232,240,0.6)', fontSize: '0.9rem' }}>{item.info}</Typography>
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </Grid>
          <Grid size={{ xs: 12, md: 7 }}>
            <Card id="contact-form" sx={{
              background: 'rgba(19, 34, 56, 0.8)',
              border: '1px solid rgba(100, 180, 255, 0.15)',
              borderRadius: 2, p: 4,
            }}>
              <Typography variant="h5" sx={{ color: '#E2E8F0', mb: 3, fontWeight: 600, fontSize: '1.25rem' }}>Send us a Message</Typography>
              <Box
                component="form"
                action={`https://formsubmit.co/${CONTACT_EMAIL}`}
                method="POST"
                sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}
              >
                {/* Spam protection: honeypot field */}
                <input type="text" name="_honey" style={{ display: 'none' }} />
                {/* Disable captcha redirect */}
                <input type="hidden" name="_captcha" value="true" />
                {/* Rate limiting message */}
                <input type="hidden" name="_autoresponse" value="Thank you for contacting Yeda AI. We've received your message and will get back to you within 24 hours." />
                <input type="hidden" name="_template" value="table" />
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField fullWidth label="Name" name="name" required variant="outlined" sx={inputStyle} />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField fullWidth label="Email" name="email" type="email" required variant="outlined" sx={inputStyle} />
                  </Grid>
                </Grid>
                <TextField fullWidth label="Subject" name="subject" variant="outlined" sx={inputStyle} />
                <TextField fullWidth label="Message" name="message" required multiline rows={4} variant="outlined" sx={inputStyle} />
                <Button type="submit" variant="contained" size="large" sx={{
                  background: 'linear-gradient(135deg, #3B82F6, #1E40AF)',
                  py: 1.5, borderRadius: '8px',
                  boxShadow: '0 4px 15px rgba(59, 130, 246, 0.3)',
                  '&:hover': { transform: 'translateY(-2px)', boxShadow: '0 6px 20px rgba(59, 130, 246, 0.4)', background: 'linear-gradient(135deg, #3B82F6, #1E40AF)' },
                }}>
                  Send Message
                </Button>
              </Box>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

export default Contact;

